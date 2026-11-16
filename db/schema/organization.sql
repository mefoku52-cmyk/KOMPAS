CREATE TABLE organization_assignment (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	task_id UUID NOT NULL, 
	assignee_user_id UUID NOT NULL, 
	role_in_task VARCHAR(64), 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(task_id) REFERENCES organization_task (id), 
	FOREIGN KEY(assignee_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_organization_assignment_assignee_user_id ON organization_assignment (assignee_user_id);

CREATE INDEX ix_organization_assignment_task_id ON organization_assignment (task_id);

CREATE INDEX ix_organization_assignment_school_id ON organization_assignment (school_id);

CREATE TABLE organization_plan (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id)
);

CREATE INDEX ix_organization_plan_school_id ON organization_plan (school_id);

CREATE TABLE organization_task (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	status VARCHAR(32) NOT NULL, 
	due_at TIMESTAMP WITH TIME ZONE, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id)
);

CREATE INDEX ix_organization_task_school_id ON organization_task (school_id);
