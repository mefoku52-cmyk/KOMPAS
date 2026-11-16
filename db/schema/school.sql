CREATE TABLE school_class_group (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	school_year_id UUID NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	grade INTEGER NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_school_class_year_name UNIQUE (school_year_id, name), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(school_year_id) REFERENCES school_year (id)
);

CREATE INDEX ix_school_class_group_school_id ON school_class_group (school_id);

CREATE INDEX ix_school_class_group_school_year_id ON school_class_group (school_year_id);

CREATE TABLE school_class_teacher (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	class_group_id UUID NOT NULL, 
	teacher_user_id UUID NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_school_class_teacher UNIQUE (school_id, class_group_id, teacher_user_id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(class_group_id) REFERENCES school_class_group (id), 
	FOREIGN KEY(teacher_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_school_class_teacher_class_group_id ON school_class_teacher (class_group_id);

CREATE INDEX ix_school_class_teacher_teacher_user_id ON school_class_teacher (teacher_user_id);

CREATE INDEX ix_school_class_teacher_school_id ON school_class_teacher (school_id);

CREATE TABLE school_enrollment (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	school_year_id UUID NOT NULL, 
	class_group_id UUID NOT NULL, 
	student_user_id UUID NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_school_enrollment_year_student UNIQUE (school_year_id, student_user_id), 
	FOREIGN KEY(school_id) REFERENCES school_school (id), 
	FOREIGN KEY(school_year_id) REFERENCES school_year (id), 
	FOREIGN KEY(class_group_id) REFERENCES school_class_group (id), 
	FOREIGN KEY(student_user_id) REFERENCES identity_user (id)
);

CREATE INDEX ix_school_enrollment_school_year_id ON school_enrollment (school_year_id);

CREATE INDEX ix_school_enrollment_student_user_id ON school_enrollment (student_user_id);

CREATE INDEX ix_school_enrollment_class_group_id ON school_enrollment (class_group_id);

CREATE INDEX ix_school_enrollment_school_id ON school_enrollment (school_id);

CREATE TABLE school_school (
	id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE school_year (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_to TIMESTAMP WITH TIME ZONE, 
	version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_school_year_school_name UNIQUE (school_id, name), 
	FOREIGN KEY(school_id) REFERENCES school_school (id)
);

CREATE INDEX ix_school_year_school_id ON school_year (school_id);
