-- Generated from SQLAlchemy model metadata for sis.

CREATE TABLE sis_identity_map (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	provider_type VARCHAR(32) NOT NULL, 
	entity_type VARCHAR(64) NOT NULL, 
	external_id VARCHAR(255) NOT NULL, 
	internal_id UUID, 
	external_key VARCHAR(512), 
	payload_hash VARCHAR(128), 
	last_seen_at TIMESTAMP WITH TIME ZONE, 
	absent_runs INTEGER NOT NULL, 
	conflict_state VARCHAR(32) NOT NULL, 
	conflict_detail JSON, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sis_identity_source_entity_external UNIQUE (source_id, entity_type, external_id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(source_id) REFERENCES sis_source (id)
);

CREATE TABLE sis_source (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	provider_type VARCHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	base_url VARCHAR(512), 
	config JSON NOT NULL, 
	secret_ref VARCHAR(255), 
	encrypted_secret TEXT, 
	is_enabled BOOLEAN NOT NULL, 
	last_sync_at TIMESTAMP WITH TIME ZONE, 
	last_success_at TIMESTAMP WITH TIME ZONE, 
	last_cursor TEXT, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sis_source_school_provider_name UNIQUE (school_id, provider_type, name), 
	FOREIGN KEY(school_id) REFERENCES school_school (id)
);

CREATE TABLE sis_sync_item (
	id UUID NOT NULL, 
	job_id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	entity_type VARCHAR(64) NOT NULL, 
	external_id VARCHAR(255), 
	internal_id UUID, 
	action VARCHAR(64) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	detail JSON NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(job_id) REFERENCES sis_sync_job (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(source_id) REFERENCES sis_source (id)
);

CREATE TABLE sis_sync_job (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	source_id UUID NOT NULL, 
	mode VARCHAR(32) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	triggered_by_user_id UUID, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	summary JSON NOT NULL, 
	error TEXT, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(source_id) REFERENCES sis_source (id), 
	FOREIGN KEY(triggered_by_user_id) REFERENCES identity_user (id)
);
