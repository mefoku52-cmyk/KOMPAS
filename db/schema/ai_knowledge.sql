CREATE TABLE ai_knowledge_context_memory (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	source_record_ref VARCHAR(255) NOT NULL, 
	content TEXT NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_ai_knowledge_context_memory_school_id ON ai_knowledge_context_memory (school_id);

CREATE TABLE ai_knowledge_source (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	source_type VARCHAR(64) NOT NULL, 
	content TEXT NOT NULL, 
	approved BOOLEAN NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_ai_knowledge_source_school_id ON ai_knowledge_source (school_id);
