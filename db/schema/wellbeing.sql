-- Generated from SQLAlchemy model metadata for wellbeing.

CREATE TABLE k17_wellbeing_observations (
	id VARCHAR(36) NOT NULL, 
	student_id VARCHAR(36) NOT NULL, 
	session_id VARCHAR(36), 
	event_type VARCHAR(50) NOT NULL, 
	metrics JSON NOT NULL, 
	inferred_state behavioralstate NOT NULL, 
	alert_level INTEGER NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);
