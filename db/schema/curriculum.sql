CREATE TABLE curriculum_subject (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_curriculum_subject_school_name UNIQUE (school_id, name), 
	FOREIGN KEY(school_id) REFERENCES school_school (id)
);

CREATE INDEX ix_curriculum_subject_school_id ON curriculum_subject (school_id);

CREATE TABLE curriculum_subject_workspace (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	subject_id UUID NOT NULL, 
	teacher_user_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_curriculum_workspace_subject_teacher UNIQUE (subject_id, teacher_user_id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(subject_id) REFERENCES curriculum_subject (id), 
	FOREIGN KEY(teacher_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_curriculum_subject_workspace_subject_id ON curriculum_subject_workspace (subject_id);

CREATE INDEX ix_curriculum_subject_workspace_school_id ON curriculum_subject_workspace (school_id);

CREATE INDEX ix_curriculum_subject_workspace_teacher_user_id ON curriculum_subject_workspace (teacher_user_id);

CREATE TABLE curriculum_topic (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	subject_id UUID NOT NULL, 
	parent_topic_id UUID, 
	name VARCHAR(255) NOT NULL, 
	grade INTEGER NOT NULL, 
	order_index INTEGER NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_curriculum_topic_subject_parent_name UNIQUE (subject_id, parent_topic_id, name), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(subject_id) REFERENCES curriculum_subject (id), 
	FOREIGN KEY(parent_topic_id) REFERENCES curriculum_topic (id)
);

CREATE INDEX ix_curriculum_topic_subject_id ON curriculum_topic (subject_id);

CREATE INDEX ix_curriculum_topic_parent_topic_id ON curriculum_topic (parent_topic_id);

CREATE INDEX ix_curriculum_topic_school_id ON curriculum_topic (school_id);

CREATE TABLE curriculum_workspace_topic_node (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	workspace_id UUID NOT NULL, 
	topic_id UUID, 
	parent_node_id UUID, 
	title VARCHAR(255) NOT NULL, 
	order_index INTEGER NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(workspace_id) REFERENCES curriculum_subject_workspace (id), 
	FOREIGN KEY(topic_id) REFERENCES curriculum_topic (id), 
	FOREIGN KEY(parent_node_id) REFERENCES curriculum_workspace_topic_node (id)
);

CREATE INDEX ix_curriculum_workspace_topic_node_school_id ON curriculum_workspace_topic_node (school_id);

CREATE INDEX ix_curriculum_workspace_topic_node_topic_id ON curriculum_workspace_topic_node (topic_id);

CREATE INDEX ix_curriculum_workspace_topic_node_parent_node_id ON curriculum_workspace_topic_node (parent_node_id);

CREATE INDEX ix_curriculum_workspace_topic_node_workspace_id ON curriculum_workspace_topic_node (workspace_id);
