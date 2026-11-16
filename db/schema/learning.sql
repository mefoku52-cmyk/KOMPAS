CREATE TABLE learning_attempt (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	task_id UUID NOT NULL, 
	student_user_id UUID NOT NULL, 
	answer TEXT NOT NULL, 
	is_correct BOOLEAN NOT NULL, 
	evaluated BOOLEAN NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(task_id) REFERENCES learning_task (id), 
	FOREIGN KEY(student_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_learning_attempt_school_id ON learning_attempt (school_id);

CREATE INDEX ix_learning_attempt_student_user_id ON learning_attempt (student_user_id);

CREATE INDEX ix_learning_attempt_task_id ON learning_attempt (task_id);

CREATE TABLE learning_mission (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	topic_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	is_verification BOOLEAN NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(topic_id) REFERENCES curriculum_topic (id)
);

CREATE INDEX ix_learning_mission_school_id ON learning_mission (school_id);

CREATE INDEX ix_learning_mission_topic_id ON learning_mission (topic_id);

CREATE TABLE learning_task (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	mission_id UUID NOT NULL, 
	task_type VARCHAR(10) NOT NULL, 
	prompt TEXT NOT NULL, 
	expected_answer TEXT NOT NULL, 
	order_index INTEGER NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(mission_id) REFERENCES learning_mission (id)
);

CREATE INDEX ix_learning_task_mission_id ON learning_task (mission_id);

CREATE INDEX ix_learning_task_school_id ON learning_task (school_id);
