export type Banner = {
	id: string;
	type: string;
	title?: string;
	content: string;
	url?: string;
	dismissible?: boolean;
	timestamp: number;
};

type Meta = {
	description?: string;
	manifest?: Record<string, string>;
}

export type PythonScript = {
	id: string;
	name: string;
	content: string;
	user_id: string;
	created_at: string;
	updated_at: string;
	meta: Meta
}

export type User = {
	id: string;
	name: string;
	role: string;
	email: string;
	created_at: string;
	updated_at: string;
	info: any;
}