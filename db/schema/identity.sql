CREATE TABLE identity_guardian_link (
	id UUID NOT NULL, 
	guardian_user_id UUID NOT NULL, 
	child_user_id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	relationship VARCHAR(64), 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_identity_guardian_child_school UNIQUE (guardian_user_id, child_user_id, school_id), 
	FOREIGN KEY(guardian_user_id) REFERENCES identity_user (id), 
	FOREIGN KEY(child_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_identity_guardian_link_school_id ON identity_guardian_link (school_id);

CREATE INDEX ix_identity_guardian_link_guardian_user_id ON identity_guardian_link (guardian_user_id);

CREATE INDEX ix_identity_guardian_link_child_user_id ON identity_guardian_link (child_user_id);

CREATE TABLE identity_role_assignment (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_identity_role_assignment_school_id ON identity_role_assignment (school_id);

CREATE INDEX ix_identity_role_assignment_user_id ON identity_role_assignment (user_id);

CREATE TABLE identity_user (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	username VARCHAR(150) NOT NULL, 
	full_name VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(512) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_identity_user_school_username UNIQUE (school_id, username)
);

CREATE INDEX ix_identity_user_school_id ON identity_user (school_id);
