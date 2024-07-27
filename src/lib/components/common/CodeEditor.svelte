<script lang="ts">
	import { basicSetup, EditorView } from 'codemirror';
	import { keymap, placeholder, ViewUpdate } from '@codemirror/view';
	import { Compartment, EditorState } from '@codemirror/state';

	import { acceptCompletion } from '@codemirror/autocomplete';
	import { indentWithTab } from '@codemirror/commands';

	import { indentUnit } from '@codemirror/language';
	import { python } from '@codemirror/lang-python';
	import { oneDark } from '@codemirror/theme-one-dark';

	import { onMount, createEventDispatcher, getContext } from 'svelte';
	import { formatPythonCode } from '$lib/apis/utils';
	import { toast } from 'svelte-sonner';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	export let boilerplate = '';
	export let value = '';
	export let readOnly = false;	// read only mode
	export let key = ''; 					// key to re-render

	let innerKey: string | null = null;

	let codeEditor: EditorView | null;

	let isDarkMode = false;
	let editorTheme = new Compartment();
	let readOnlyConfig = new Compartment();

	export const formatPythonCodeHandler = async () => {
		if (codeEditor) {
			const res = await formatPythonCode(value).catch((error) => {
				toast.error(error);
				return null;
			});

			if (res && res.code) {
				const formattedCode = res.code;
				codeEditor.dispatch({
					changes: [{ from: 0, to: codeEditor.state.doc.length, insert: formattedCode }]
				});

				toast.success($i18n.t('Code formatted successfully'));
				return true;
			}
			return false;
		}
		return false;
	};

	const onUpdate = (e: ViewUpdate) => {
		if (e.docChanged && !readOnly) {
			value = e.state.doc.toString();
		}
	};

	let extensions = [
		basicSetup,
		keymap.of([{ key: 'Tab', run: acceptCompletion }, indentWithTab]),
		python(),
		indentUnit.of('    '),
		placeholder('Enter your code here...'),
		EditorView.updateListener.of(onUpdate),
		editorTheme.of([]),
		readOnlyConfig.of(EditorState.readOnly.of(readOnly))
	];

	$: {
		codeEditor?.dispatch({
			effects: readOnlyConfig.reconfigure(EditorState.readOnly.of(readOnly))
		});
	}

	$: if (key !== innerKey) {
		innerKey = key;
		codeEditor?.dispatch({
			changes: [{ from: 0, to: codeEditor.state.doc.length, insert: value }]
		})
	}

	onMount(() => {
		console.log(value);
		if (value === '') {
			value = boilerplate;
		}

		codeEditor = new EditorView({
			state: EditorState.create({
				doc: value,
				extensions: extensions
			}),
			parent: document.getElementById('code-textarea')
		});

		// Check if html class has dark mode
		isDarkMode = document.documentElement.classList.contains('dark');

		if (isDarkMode) {
			codeEditor?.dispatch({
				effects: editorTheme.reconfigure(oneDark)
			});
		}

		// listen to html class changes this should fire only when dark mode is toggled
		const observer = new MutationObserver((mutations) => {
			mutations.forEach((mutation) => {
				if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
					const _isDarkMode = document.documentElement.classList.contains('dark');

					if (_isDarkMode !== isDarkMode) {
						isDarkMode = _isDarkMode;
						if (_isDarkMode) {
							codeEditor?.dispatch({
								effects: editorTheme.reconfigure([oneDark])
							});
						} else {
							codeEditor?.dispatch({
								effects: editorTheme.reconfigure([])
							});
						}
					}
				}
			});
		});

		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		const keydownHandler = async (e) => {
			if ((e.ctrlKey || e.metaKey) && e.key === 's') {
				e.preventDefault();
				dispatch('save');
			}

			// Format code when Ctrl + Shift + F is pressed
			if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'f') {
				e.preventDefault();
				await formatPythonCodeHandler();
			}
		};

		document.addEventListener('keydown', keydownHandler);
		return () => {
			observer.disconnect();
			document.removeEventListener('keydown', keydownHandler);
		};
	});
</script>

<div id="code-textarea" class="h-full w-full" />
