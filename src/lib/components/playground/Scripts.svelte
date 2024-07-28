<script lang="ts">
	import { copyToClipboard } from '$lib/utils';
	import { saveAs } from 'file-saver';
	import { toast } from 'svelte-sonner';
	import { type Writable } from 'svelte/store';
	import { v4 as uuidv4 } from 'uuid';

	import PyodideWorker from '$lib/workers/pyodide.worker?worker';

	import { pythonScripts, user } from '$lib/stores';
	import { type PythonScript } from '$lib/types';
	import { getContext, onMount } from 'svelte';

	import {
		createNewPyScripts,
		deletePyScriptById,
		getPyScriptById,
		listPyScripts,
		queryPyScriptsByName,
		updatePyScriptById
	} from '$lib/apis/scripts';

	import { getUserById } from '$lib/apis/users';
	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import type { i18n as i18nType } from 'i18next';
	import CodeEditor from '../common/CodeEditor.svelte';
	import ConfirmDialog from '../common/ConfirmDialog.svelte';

	const boilerplate = `# Python Script Example - Quick Sort
def quicksort(arr):
	if len(arr) <= 1:
		return arr
	else:
		pivot = arr[len(arr) // 2]
		left = [x for x in arr if x < pivot]
		middle = [x for x in arr if x == pivot]
		right = [x for x in arr if x > pivot]
		return quicksort(left) + middle + quicksort(right)

# Example usage
arr = [3, 6, 8, 10, 1, 2, 1]
print("Original array:", arr)
sorted_arr = quicksort(arr)
print("Sorted array:", sorted_arr)
`;

	let stdout: string | null = null;
	let stderr: string | null = null;
	let result: string | null = null;
	let executing = false;

	const executePythonAsWorker = async (code: string) => {
		result = null;
		stdout = null;
		stderr = null;

		executing = true;

		let packages = [
			code.includes('requests') ? 'requests' : null,
			code.includes('bs4') ? 'beautifulsoup4' : null,
			code.includes('numpy') ? 'numpy' : null,
			code.includes('pandas') ? 'pandas' : null,
			code.includes('sklearn') ? 'scikit-learn' : null,
			code.includes('scipy') ? 'scipy' : null,
			code.includes('re') ? 'regex' : null,
			code.includes('seaborn') ? 'seaborn' : null
		].filter(Boolean);

		console.log(packages);
		const pyodideWorker = new PyodideWorker();

		pyodideWorker.postMessage({
			id: uuidv4(),
			code: code,
			packages: packages
		});

		setTimeout(() => {
			if (executing) {
				executing = false;
				stderr = 'Execution Time Limit Exceeded';
				pyodideWorker.terminate();
			}
		}, 60000);

		pyodideWorker.onmessage = (event) => {
			console.log('pyodideWorker.onmessage', event);
			const { id, ...data } = event.data;

			console.log(id, data);

			data['stdout'] && (stdout = data['stdout']);
			data['stderr'] && (stderr = data['stderr']);
			data['result'] && (result = data['result']);

			executing = false;
		};

		pyodideWorker.onerror = (event) => {
			console.log('pyodideWorker.onerror', event);
			executing = false;
		};
	};

	const i18n = getContext<Writable<i18nType>>('i18n');

	let scriptImportInputElement: HTMLInputElement;
	let importFiles: FileList | null = null;

	let showConfirm = false;
	let showDeleteConfirm = false;
	let query = '';
	let ownerName: string | null = null;

	let scriptList: PythonScript[] = $pythonScripts;
	let totalScripts: number = 0;

	let timeoutToQuery: Timer | null = null; // For debouncing

	$: if (query !== '') {
		if (timeoutToQuery) {
			clearTimeout(timeoutToQuery);
		}
		timeoutToQuery = setTimeout(async () => {
			timeoutToQuery = null;

			scriptList = (await queryPyScriptsByName(localStorage.token, query.trim())).scripts;
		}, 1000);
	} else {
		scriptList = $pythonScripts;
	}

	let selectedScript: PythonScript | null = null;
	let editing = false;

	let showingScript: PythonScript; // For better typing

	$: if (selectedScript) {
		showingScript = selectedScript;
	}

	const onSearchKeyUp = async (e: KeyboardEvent) => {
		if (e.key === 'Enter') {
			if (timeoutToQuery) {
				clearTimeout(timeoutToQuery);
			}
			timeoutToQuery = null;
			query = query.trim();
			scriptList = (await queryPyScriptsByName(localStorage.token, query)).scripts;
		}
	};

	const onUploadPythonFile = () => {
		const reader = new FileReader();

		reader.onload = async (event) => {
			const newScripts = newPyScript();
			newScripts.name = importFiles?.[0].name || '';
			newScripts.content = event?.target?.result?.toString() || '';
			selectedScript = newScripts;
			showingScript = newScripts;

			await onMutatingScript();

			toast.success($i18n.t('Python script imported successfully'));
			const listRes = await listPyScripts(localStorage.token).catch((error) => {
				toast.error(error);
				return null;
			});
			if (listRes) {
				pythonScripts.set(listRes.scripts);
				totalScripts = listRes.total;
			}
		};

		if (importFiles) {
			reader.readAsText(importFiles[0]);
		}
	};

	async function downloadScript() {
		const blob = new Blob([showingScript.content], { type: 'text/plain;charset=utf-8' });
		saveAs(blob, showingScript.name);
	}

	function newPyScript(): PythonScript {
		return {
			id: '',
			name: '',
			content: '',
			meta: {
				description: ''
			},
			created_at: '',
			updated_at: '',
			user_id: ''
		};
	}

	async function prepareNewScript() {
		const newScript = newPyScript();
		newScript.content = boilerplate;
		selectedScript = newScript;
		editing = true;
	}

	async function onMutatingScript() {
		if (!showingScript.name) {
			toast.error($i18n.t('Name is required'));
			return;
		}
		if (!showingScript.content) {
			toast.error($i18n.t('Content is required'));
			return;
		}
		if (showingScript.id !== '') {
			return updatePyScriptById(localStorage.token, showingScript.id, showingScript)
				.then(async (res) => {
					toast.success($i18n.t('Python script updated successfully'));
					pythonScripts.set((await listPyScripts(localStorage.token)).scripts);
					editing = false;
					selectedScript = res;
					return res;
				})
				.catch((error) => {
					toast.error(error);
				});
		} else {
			return createNewPyScripts(localStorage.token, showingScript)
				.then(async (res) => {
					toast.success($i18n.t('Python script created successfully'));
					pythonScripts.set((await listPyScripts(localStorage.token)).scripts);
					editing = false;
					selectedScript = res;
					return res;
				})
				.catch((error) => {
					toast.error(error);
				});
		}
	}

	async function loadScriptContent(id: string) {
		editing = false;
		stdout = stderr = result = null;
		executing = false;
		const res = await getPyScriptById(localStorage.token, id).catch((error) => {
			toast.error(error);
			return null;
		});
		if (res) {
			selectedScript = res;
			showingScript = res;
		}
		if ($user?.role === 'admin' && res?.user_id !== $user?.id) {
			await getUserById(localStorage.token, res?.user_id).then((user) => {
				ownerName = user?.name;
			});
		} else {
			ownerName = null;
		}
	}

	const deleteHandler = async (s: PythonScript) => {
		const res = await deletePyScriptById(localStorage.token, s.id).catch((error) => {
			toast.error(error);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Python script deleted successfully'));
			pythonScripts.set((await listPyScripts(localStorage.token)).scripts);
		}
		selectedScript = null;
	};
</script>

<input
	id="scripts-import-input"
	bind:this={scriptImportInputElement}
	bind:files={importFiles}
	type="file"
	accept=".py"
	hidden
	on:change={() => {
		console.log(importFiles);
		showConfirm = true;
	}}
/>

<div class="h-full flex flex-col overflow-auto">
	<!-- Panel -->
	<div class="flex flex-1 h-[calc(100%-64px)]">
		<!-- Side Bar -->
		<div class="border-r dark:border-gray-850 pr-2">
			<!-- Search -->
			<div class="flex w-80 space-x-2">
				<div class="flex flex-1">
					<div class="self-center ml-1 mr-3">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								fill-rule="evenodd"
								d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<input
						class="w-full text-sm pr-4 py-1 rounded-r-xl outline-none bg-transparent"
						bind:value={query}
						on:keyup={onSearchKeyUp}
						placeholder={$i18n.t('Search By Name Prefix')}
					/>
				</div>

				<!-- Upload Button -->
				<button
					class="px-2 py-2 rounded-xl border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1"
					on:click={() => {
						scriptImportInputElement.click();
					}}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 16 16"
						fill="currentColor"
						class="w-4 h-4"
					>
						<path
							fill-rule="evenodd"
							d="M4 2a1.5 1.5 0 0 0-1.5 1.5v9A1.5 1.5 0 0 0 4 14h8a1.5 1.5 0 0 0 1.5-1.5V6.621a1.5 1.5 0 0 0-.44-1.06L9.94 2.439A1.5 1.5 0 0 0 8.878 2H4Zm4 9.5a.75.75 0 0 1-.75-.75V8.06l-.72.72a.75.75 0 0 1-1.06-1.06l2-2a.75.75 0 0 1 1.06 0l2 2a.75.75 0 1 1-1.06 1.06l-.72-.72v2.69a.75.75 0 0 1-.75.75Z"
							clip-rule="evenodd"
						/>
					</svg>
				</button>
				<!-- Plus Button -->
				<button
					class="px-2 py-2 rounded-xl border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1"
					on:click={() => {
						prepareNewScript();
					}}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 16 16"
						fill="currentColor"
						class="w-4 h-4"
					>
						<path
							d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z"
						/>
					</svg>
				</button>
			</div>
			<hr class="w-80 dark:border-gray-850 my-2.5" />

			<!-- List -->
			<div class="mb-5 max-h-[calc(100%-64px)] overflow-x-hidden">
				{#each scriptList as script}
					<button
						class={`flex space-x-4 cursor-pointer w-80 px-3 py-2 my-1 dark:hover:bg-white/5 hover:bg-black/5 rounded-xl ${
							selectedScript && selectedScript.id === script.id ? 'dark:bg-white/5 bg-black/5' : ''
						}`}
						on:click={async () => {
							await loadScriptContent(script.id);
						}}
					>
						<div class="flex flex-1 space-x-3.5 cursor-pointer w-80">
							<div class="flex items-center text-left w-full">
								<div class="flex-1 self-center pl-1">
									<div class="font-semibold flex items-center gap-1.5">
										<div class="line-clamp-1">
											{script.name}
										</div>
										{#if $user?.role === 'admin' && $user?.id === script.user_id}
											<div
												class=" ml-auto text-xs font-bold px-1 rounded uppercase shrink-0 bg-gray-500/20 text-gray-700 dark:text-gray-200"
											>
												{$i18n.t('Yours')}
											</div>
										{/if}
									</div>

									<div class="flex gap-1.5">
										<div class="text-xs overflow-hidden text-ellipsis line-clamp-1">
											{script.meta.description || $i18n.t('(No description)')}
										</div>
									</div>

									<div class="text-xs text-gray-500 dark:text-gray-400">
										{$i18n.t('Updated at')}
										{new Date(parseInt(script.updated_at) * 1000).toLocaleString()}
									</div>
								</div>
							</div>
						</div>
					</button>
				{/each}
			</div>
		</div>

		<!-- Editor -->
		<div class="ml-2 flex-1 h-full flex flex-col">
			{#if selectedScript}
				<!-- Operation Panel -->
				<div class="mb-4">
					<div class="flex justify-between items-center">
						<div class="font-semibold self-center">
							{showingScript.id !== ''
								? editing
									? $i18n.t('Edit Python Script')
									: $i18n.t('Python Script Details') + (ownerName ? ` (Owned by ${ownerName})` : '')
								: $i18n.t('Create Python Script')}
						</div>
						<div class=" flex space-x-2">
							{#if !editing && showingScript.id !== ''}
								<button
									class="px-2 py-1 rounded-md border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1"
									on:click={() => {
										showDeleteConfirm = true;
									}}
								>
									{$i18n.t('Delete')}
								</button>

								<button
									class="px-2 py-1 rounded-md border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1"
									on:click={async () => {
										await downloadScript();
									}}
								>
									{$i18n.t('Download')}
								</button>

								<button
									class="px-2 py-1 rounded-md border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1"
									on:click={() => {
										editing = true;
									}}
								>
									{$i18n.t('Edit')}
								</button>
							{:else}
								<button
									class="px-2 py-1 rounded-md border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1"
									on:click={async () => {
										if (selectedScript && selectedScript.id === '') {
											selectedScript = null;
										} else {
											await loadScriptContent(showingScript.id);
										}
										editing = false;
									}}
								>
									{$i18n.t('Cancel')}
								</button>
								<button
									class="px-2 py-1 rounded-md border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1"
									on:click={() => {
										onMutatingScript();
									}}
								>
									{showingScript.id === '' ? $i18n.t('Create') : $i18n.t('Save')}
								</button>
							{/if}
						</div>
					</div>
					<!-- inputs for name and description -->
					<div class="flex flex-col gap-2 mt-2">
						<div class="flex w-full items-center">
							<label for="name" class="text-sm text-gray-500 dark:text-gray-400 mr-4 w-20">
								{$i18n.t('Name')}
							</label>
							<input
								class="flex-1 px-3 py-2 text-sm font-medium bg-gray-50 dark:bg-gray-850 dark:text-gray-200 rounded-lg outline-none"
								type="text"
								id="name"
								placeholder="Script Name (e.g. quicksort.py)"
								required
								readonly={!editing}
								bind:value={showingScript.name}
							/>
						</div>
						<div class="flex w-full items-center">
							<label for="description" class="text-sm text-gray-500 dark:text-gray-400 mr-4 w-20">
								{$i18n.t('Description')}
							</label>
							<input
								class="flex-1 px-3 py-2 text-sm font-medium bg-gray-50 dark:bg-gray-850 dark:text-gray-200 rounded-lg outline-none"
								type="text"
								id="description"
								placeholder="Description of the script (e.g. Sorts an array using quicksort)"
								required
								readonly={!editing}
								bind:value={showingScript.meta.description}
							/>
						</div>
					</div>
				</div>

				<!-- Code Editor -->
				<div class="rounded-t-lg dark:bg-white bg-gray-50 px-2">
					<div class="flex justify-between items-center text-sm text-gray-600">
						<div class="font-semibold self-center">{$i18n.t('Source Code')}</div>
						<div class="flex space-x-2">
							<button
								class=" text-blue-700"
								on:click={() => {
									executePythonAsWorker(showingScript.content);
								}}>{$i18n.t('Run')}</button
							>
							<button
								class=" text-blue-700"
								on:click={async () => {
									try {
										await copyToClipboard(showingScript.content);
										toast.success($i18n.t('Copied to clipboard'));
									} catch (error) {
										console.log(error);
										toast.error($i18n.t('Failed to copy the code to clipboard'));
									}
								}}>{$i18n.t('Copy')}</button
							>
						</div>
					</div>
				</div>
				<div class="flex-1 max-h-[calc(100%-160px)] min-h-0 flex flex-col">
					<CodeEditor
						bind:value={showingScript.content}
						readOnly={!editing}
						key={selectedScript.id}
					/>
				</div>
				{#if executing}
					<div class="bg-[#202123] text-white px-4 py-4 rounded-b-lg">
						<div class=" text-gray-500 text-xs mb-1">{$i18n.t('STDOUT/STDERR')}</div>
						<div class="text-sm">{$i18n.t('Running')}...</div>
					</div>
				{:else if stdout || stderr || result}
					<div class="bg-[#202123] text-white px-4 py-4 rounded-b-lg">
						<div class=" text-gray-500 text-xs mb-1">{$i18n.t('STDOUT/STDERR')}</div>
						<pre class="text-sm">{stdout || stderr || result}</pre>
					</div>
				{/if}
			{:else}
				<div class="flex flex-col items-center justify-center h-full gap-y-4">
					<button
						class="w-40 px-2 py-2 rounded-xl border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1 justify-center"
						on:click={() => {
							scriptImportInputElement.click();
						}}
					>
						<span>{$i18n.t('Upload new script')}</span>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 16 16"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								fill-rule="evenodd"
								d="M4 2a1.5 1.5 0 0 0-1.5 1.5v9A1.5 1.5 0 0 0 4 14h8a1.5 1.5 0 0 0 1.5-1.5V6.621a1.5 1.5 0 0 0-.44-1.06L9.94 2.439A1.5 1.5 0 0 0 8.878 2H4Zm4 9.5a.75.75 0 0 1-.75-.75V8.06l-.72.72a.75.75 0 0 1-1.06-1.06l2-2a.75.75 0 0 1 1.06 0l2 2a.75.75 0 1 1-1.06 1.06l-.72-.72v2.69a.75.75 0 0 1-.75.75Z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
					<button
						class="w-40 px-2 py-2 rounded-xl border border-gray-200 dark:border-gray-600 dark:border-0 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 transition font-medium text-sm flex items-center space-x-1 justify-center"
						on:click={() => {
							prepareNewScript();
						}}
					>
						<span>
							{$i18n.t('Create new script')}
						</span>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 16 16"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z"
							/>
						</svg>
					</button>
				</div>
			{/if}
		</div>
	</div>
</div>

<DeleteConfirmDialog
	bind:show={showDeleteConfirm}
	title={$i18n.t('Delete the python script?')}
	on:confirm={() => {
		deleteHandler(showingScript);
	}}
>
	<div class="text-sm text-gray-500">
		{$i18n.t('This will delete')} <span class=" font-semibold">{showingScript.name}</span>.
	</div>
</DeleteConfirmDialog>

<ConfirmDialog bind:show={showConfirm} on:confirm={onUploadPythonFile}>
	<div class="text-sm text-gray-500">
		<div class="bg-yellow-500/20 text-yellow-700 dark:text-yellow-200 rounded-lg px-4 py-3">
			<div>Please carefully review the following warnings:</div>

			<ul class="mt-1 list-disc pl-4 text-xs">
				<li>Python Playground allow arbitrary code execution.</li>
				<li>Do not upload scripts from sources you do not fully trust.</li>
			</ul>
		</div>

		<div class="my-3">
			I acknowledge that I have read and I understand the implications of my action. I am aware of
			the risks associated with executing arbitrary code and I have verified the trustworthiness of
			the source.
		</div>
	</div>
</ConfirmDialog>
