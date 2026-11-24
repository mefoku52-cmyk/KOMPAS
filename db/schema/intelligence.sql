-- Generated from SQLAlchemy model metadata for intelligence.

CREATE TABLE il_audit (
	id UUID NOT NULL, 
	ts TIMESTAMP WITH TIME ZONE NOT NULL, 
	actor VARCHAR(128) NOT NULL, 
	action VARCHAR(128) NOT NULL, 
	entity_type VARCHAR(64), 
	entity_id VARCHAR(128), 
	details JSON NOT NULL, 
	school_id UUID, 
	PRIMARY KEY (id)
);

CREATE TABLE il_communication (
	id UUID NOT NULL, 
	initiative_id UUID NOT NULL, 
	channel VARCHAR(32) NOT NULL, 
	content_key VARCHAR(128) NOT NULL, 
	locale VARCHAR(8) NOT NULL, 
	payload JSON NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	sent_at TIMESTAMP WITH TIME ZONE, 
	acknowledged_at TIMESTAMP WITH TIME ZONE, 
	school_id UUID, 
	PRIMARY KEY (id)
);

CREATE TABLE il_context_memory (
	id UUID NOT NULL, 
	entity_type VARCHAR(64) NOT NULL, 
	entity_id VARCHAR(128) NOT NULL, 
	context_type VARCHAR(64) NOT NULL, 
	context JSON NOT NULL, 
	confidence FLOAT, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	source_event_id UUID, 
	source_record_ref VARCHAR(255), 
	school_id UUID, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE il_dead_letter (
	id UUID NOT NULL, 
	event_id UUID NOT NULL, 
	handler VARCHAR(128) NOT NULL, 
	payload JSON NOT NULL, 
	error TEXT NOT NULL, 
	retry_count INTEGER NOT NULL, 
	last_attempt_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	school_id UUID, 
	PRIMARY KEY (id)
);

CREATE TABLE il_hypothesis (
	id UUID NOT NULL, 
	situation_id UUID, 
	entity_type VARCHAR(64) NOT NULL, 
	entity_id VARCHAR(128) NOT NULL, 
	hypothesis_text TEXT NOT NULL, 
	confidence FLOAT NOT NULL, 
	evidence JSON NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	validated_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	school_id UUID, 
	PRIMARY KEY (id)
);

CREATE TABLE il_inbox (
	id UUID NOT NULL, 
	event_id UUID NOT NULL, 
	handler VARCHAR(128) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	attempts INTEGER NOT NULL, 
	last_error TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	processed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_il_inbox_event_handler UNIQUE (event_id, handler)
);

CREATE TABLE il_initiative (
	id UUID NOT NULL, 
	situation_id UUID, 
	entity_type VARCHAR(64) NOT NULL, 
	entity_id VARCHAR(128) NOT NULL, 
	action_type VARCHAR(64) NOT NULL, 
	decision VARCHAR(32) NOT NULL, 
	recipient_user_id UUID, 
	recipient_role VARCHAR(32), 
	status VARCHAR(32) NOT NULL, 
	reason TEXT NOT NULL, 
	urgency VARCHAR(16) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	decided_at TIMESTAMP WITH TIME ZONE, 
	decided_by VARCHAR(128), 
	dismissed_at TIMESTAMP WITH TIME ZONE, 
	school_id UUID, 
	PRIMARY KEY (id)
);

CREATE TABLE il_outbox (
	id UUID NOT NULL, 
	event_id UUID NOT NULL, 
	event_type VARCHAR(128) NOT NULL, 
	payload JSON NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	attempts INTEGER NOT NULL, 
	last_error TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	processed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_il_outbox_event_id UNIQUE (event_id)
);

CREATE TABLE il_outcome (
	id UUID NOT NULL, 
	initiative_id UUID NOT NULL, 
	outcome VARCHAR(32) NOT NULL, 
	metrics JSON NOT NULL, 
	feedback_source VARCHAR(32), 
	evaluated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	school_id UUID, 
	PRIMARY KEY (id)
);

CREATE TABLE il_perception_event (
	id UUID NOT NULL, 
	event_id UUID NOT NULL, 
	event_type VARCHAR(128) NOT NULL, 
	source VARCHAR(64) NOT NULL, 
	payload JSON NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	processed_at TIMESTAMP WITH TIME ZONE, 
	processing_status VARCHAR(32) NOT NULL, 
	school_id UUID, 
	correlation_id UUID, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE il_prediction (
	id UUID NOT NULL, 
	hypothesis_id UUID, 
	entity_id VARCHAR(128) NOT NULL, 
	prediction_text TEXT NOT NULL, 
	confidence FLOAT NOT NULL, 
	uncertainty VARCHAR(16) NOT NULL, 
	alternatives JSON NOT NULL, 
	outcome VARCHAR(32), 
	evaluated_at TIMESTAMP WITH TIME ZONE, 
	school_id UUID, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);
