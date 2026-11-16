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

CREATE INDEX ix_organization_assignment_school_id ON organization_assignment (school_id);

CREATE INDEX ix_organization_assignment_assignee_user_id ON organization_assignment (assignee_user_id);

CREATE INDEX ix_organization_assignment_task_id ON organization_assignment (task_id);

CREATE TABLE organization_operation_request (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	requester_user_id UUID NOT NULL, 
	request_type VARCHAR(32) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	status VARCHAR(11) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(requester_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_organization_operation_request_school_id ON organization_operation_request (school_id);

CREATE INDEX ix_organization_operation_request_requester_user_id ON organization_operation_request (requester_user_id);

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

CREATE TABLE organization_project (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	status VARCHAR(32) NOT NULL, 
	owner_user_id UUID NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(owner_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_organization_project_school_id ON organization_project (school_id);

CREATE INDEX ix_organization_project_owner_user_id ON organization_project (owner_user_id);

CREATE TABLE organization_project_member (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_organization_project_member UNIQUE (project_id, user_id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(project_id) REFERENCES organization_project (id), 
	FOREIGN KEY(user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_organization_project_member_project_id ON organization_project_member (project_id);

CREATE INDEX ix_organization_project_member_school_id ON organization_project_member (school_id);

CREATE INDEX ix_organization_project_member_user_id ON organization_project_member (user_id);

CREATE TABLE organization_project_submission (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	task_id UUID NOT NULL, 
	submitted_by_user_id UUID NOT NULL, 
	content TEXT NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(task_id) REFERENCES organization_project_task (id), 
	FOREIGN KEY(submitted_by_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_organization_project_submission_submitted_by_user_id ON organization_project_submission (submitted_by_user_id);

CREATE INDEX ix_organization_project_submission_task_id ON organization_project_submission (task_id);

CREATE INDEX ix_organization_project_submission_school_id ON organization_project_submission (school_id);

CREATE TABLE organization_project_task (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	status VARCHAR(32) NOT NULL, 
	assignee_user_id UUID, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(project_id) REFERENCES organization_project (id), 
	FOREIGN KEY(assignee_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_organization_project_task_school_id ON organization_project_task (school_id);

CREATE INDEX ix_organization_project_task_assignee_user_id ON organization_project_task (assignee_user_id);

CREATE INDEX ix_organization_project_task_project_id ON organization_project_task (project_id);

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
