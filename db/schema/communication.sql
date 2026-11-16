CREATE TABLE communication_message (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	thread_id UUID NOT NULL, 
	sender_user_id UUID NOT NULL, 
	body TEXT NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(thread_id) REFERENCES communication_thread (id), 
	FOREIGN KEY(sender_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_communication_message_school_id ON communication_message (school_id);

CREATE INDEX ix_communication_message_sender_user_id ON communication_message (sender_user_id);

CREATE INDEX ix_communication_message_thread_id ON communication_message (thread_id);

CREATE TABLE communication_thread (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	subject VARCHAR(255) NOT NULL, 
	is_private BOOLEAN NOT NULL, 
	created_by_user_id UUID NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_communication_thread_school_id ON communication_thread (school_id);

CREATE INDEX ix_communication_thread_created_by_user_id ON communication_thread (created_by_user_id);

CREATE TABLE communication_thread_participant (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	thread_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_communication_thread_user UNIQUE (thread_id, user_id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(thread_id) REFERENCES communication_thread (id), 
	FOREIGN KEY(user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_communication_thread_participant_school_id ON communication_thread_participant (school_id);

CREATE INDEX ix_communication_thread_participant_user_id ON communication_thread_participant (user_id);

CREATE INDEX ix_communication_thread_participant_thread_id ON communication_thread_participant (thread_id);
