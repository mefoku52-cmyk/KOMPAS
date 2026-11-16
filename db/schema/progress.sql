CREATE TABLE progress_student_profile (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	student_user_id UUID NOT NULL, 
	school_year_id UUID NOT NULL, 
	grade INTEGER NOT NULL, 
	label VARCHAR(255), 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_progress_student_profile_student_year_version UNIQUE (student_user_id, school_year_id, version), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(student_user_id) REFERENCES identity_user (id), 
	FOREIGN KEY(school_year_id) REFERENCES school_year (id)
);

CREATE INDEX ix_progress_student_profile_school_id ON progress_student_profile (school_id);

CREATE INDEX ix_progress_student_profile_school_year_id ON progress_student_profile (school_year_id);

CREATE INDEX ix_progress_student_profile_student_user_id ON progress_student_profile (student_user_id);
