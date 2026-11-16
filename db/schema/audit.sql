CREATE TABLE audit_event_log (
	id UUID NOT NULL, 
	event_type VARCHAR(128) NOT NULL, 
	school_id UUID, 
	payload TEXT NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_audit_event_log_event_type ON audit_event_log (event_type);

CREATE INDEX ix_audit_event_log_school_id ON audit_event_log (school_id);

CREATE TABLE audit_log (
	id UUID NOT NULL, 
	timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
	principal_id UUID, 
	principal_role VARCHAR(32), 
	school_id UUID, 
	action VARCHAR(128) NOT NULL, 
	resource VARCHAR(255) NOT NULL, 
	purpose VARCHAR(255), 
	outcome VARCHAR(32) NOT NULL, 
	details TEXT, 
	prev_hash VARCHAR(64) NOT NULL, 
	record_hash VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (record_hash)
);

CREATE INDEX ix_audit_log_school_id ON audit_log (school_id);

CREATE INDEX ix_audit_log_principal_id ON audit_log (principal_id);
