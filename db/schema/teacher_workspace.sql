CREATE TABLE teacher_workspace_assistant_draft (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	teacher_user_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	draft_type VARCHAR(32) NOT NULL, 
	content TEXT NOT NULL, 
	status VARCHAR(22) NOT NULL, 
	source_refs TEXT, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(teacher_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_teacher_workspace_assistant_draft_teacher_user_id ON teacher_workspace_assistant_draft (teacher_user_id);

CREATE INDEX ix_teacher_workspace_assistant_draft_school_id ON teacher_workspace_assistant_draft (school_id);

CREATE TABLE teacher_workspace_library_item (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	owner_teacher_user_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	archived BOOLEAN NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(owner_teacher_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_teacher_workspace_library_item_owner_teacher_user_id ON teacher_workspace_library_item (owner_teacher_user_id);

CREATE INDEX ix_teacher_workspace_library_item_school_id ON teacher_workspace_library_item (school_id);

CREATE TABLE teacher_workspace_library_tag (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	item_id UUID NOT NULL, 
	tag VARCHAR(64) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_teacher_workspace_library_item_tag UNIQUE (item_id, tag), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(item_id) REFERENCES teacher_workspace_library_item (id)
);

CREATE INDEX ix_teacher_workspace_library_tag_school_id ON teacher_workspace_library_tag (school_id);

CREATE INDEX ix_teacher_workspace_library_tag_item_id ON teacher_workspace_library_tag (item_id);

CREATE TABLE teacher_workspace_library_version (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	item_id UUID NOT NULL, 
	version_number INTEGER NOT NULL, 
	storage_key VARCHAR(512), 
	content_text TEXT, 
	note VARCHAR(255), 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_teacher_workspace_library_item_version UNIQUE (item_id, version_number), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(item_id) REFERENCES teacher_workspace_library_item (id)
);

CREATE INDEX ix_teacher_workspace_library_version_school_id ON teacher_workspace_library_version (school_id);

CREATE INDEX ix_teacher_workspace_library_version_item_id ON teacher_workspace_library_version (item_id);
