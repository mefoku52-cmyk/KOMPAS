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
