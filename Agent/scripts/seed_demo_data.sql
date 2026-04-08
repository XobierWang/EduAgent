# @XobierWang

INSERT OR IGNORE INTO students (
  student_code,
  full_name,
  gender,
  date_of_birth,
  phone,
  id_number,
  address,
  emergency_contact_name,
  emergency_contact_phone
) VALUES
  ('S2024001', 'Alex Zhang', 'male', '2005-03-12', '13800000001', '310101200503121234', 'Room 101, Building 3, East Campus', 'Li Zhang', '13900000001'),
  ('S2024002', 'Emma Li', 'female', '2004-08-21', '13800000002', '310101200408211234', 'Room 202, Building 5, West Campus', 'Qiang Wang', '13900000002'),
  ('S2024003', 'Michael Chen', 'male', '2005-11-05', '13800000003', '310101200511051234', 'Room 305, Building 1, North Campus', 'Fang Wang', '13900000003'),
  ('S2024004', 'Sophia Zhao', 'female', '2004-06-17', '13800000004', '310101200406171234', 'Room 108, Building 2, South Campus', 'Hai Zhao', '13900000004'),
  ('S2024005', 'David Sun', 'male', '2005-09-03', '13800000005', '310101200509031234', 'Room 412, Building 4, East Campus', 'Lihua Sun', '13900000005'),
  ('S2024006', 'Grace Liu', 'female', '2006-12-26', '13800000006', '310101200612261234', 'Room 201, Building 6, West Campus', 'Guoqing Liu', '13900000006'),
  ('S2024007', 'James Wu', 'male', '2004-04-11', '13800000007', '310101200404111234', 'Room 503, Building 3, North Campus', 'Min Wu', '13900000007'),
  ('S2024008', 'Olivia He', 'female', '2005-01-29', '13800000008', '310101200501291234', 'Room 307, Building 1, South Campus', 'Jianping He', '13900000008');

INSERT OR IGNORE INTO course_records (
  student_id,
  course_code,
  assessment,
  objective,
  performance,
  background,
  study_plan,
  teacher,
  recorded_at
) VALUES
  (
    (SELECT id FROM students WHERE student_code = 'S2024001'),
    'CR0001',
    'Strong grasp of differential calculus',
    'Master differentiation techniques for polynomial functions',
    'Scored 92/100 on midterm, minor errors in chain rule application',
    'Completed pre-calculus with A grade last semester',
    'Focus on integration techniques for next unit',
    'Prof. Wang',
    '2026-02-18 09:30:00'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024002'),
    'CR0002',
    'Needs improvement in linear algebra fundamentals',
    'Understand matrix operations and eigenvalue computation',
    'Struggling with matrix diagonalization, scored 65/100',
    'Strong background in basic algebra, first exposure to linear algebra',
    'Additional practice sessions on eigenvalues, weekly quiz review',
    'Prof. Zhou',
    '2026-01-12 14:00:00'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024003'),
    'CR0003',
    'Excellent programming skills in Python',
    'Complete data structures and algorithms coursework',
    'Finished all lab assignments ahead of schedule, top of class',
    'Self-taught Python basics, participated in coding competition',
    'Recommend advanced algorithms track next semester',
    'Prof. Chen',
    '2026-03-01 10:15:00'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024004'),
    'CR0004',
    'Making steady progress in English composition',
    'Write well-structured argumentative essays',
    'Grammar accuracy improved from 70% to 85% this semester',
    'Intermediate English proficiency, better at reading than writing',
    'Weekly writing prompts, peer review sessions',
    'Prof. Xu',
    '2026-02-05 11:20:00'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024005'),
    'CR0005',
    'Solid understanding of classical mechanics',
    'Apply Newtonian mechanics to solve multi-body problems',
    'Lab reports are consistently detailed, theoretical work needs improvement',
    'Completed introductory physics with B+',
    'Extra problem sets on rotational dynamics, tutoring sessions',
    'Prof. Zheng',
    '2026-02-22 15:40:00'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024006'),
    'CR0006',
    'Outstanding progress in organic chemistry',
    'Master reaction mechanisms for carbonyl compounds',
    'Perfect score on laboratory practical, 88% on theory exam',
    'Completed general chemistry with distinction',
    'Research project on green synthesis methods',
    'Prof. Huang',
    '2026-03-08 09:45:00'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024007'),
    'CR0007',
    'Moderate performance in statistics',
    'Understand hypothesis testing and regression analysis',
    'Good at data visualization, weak on probability theory foundations',
    'Basic math background, no prior statistics experience',
    'Focus on probability distributions, practice with real datasets',
    'Prof. Song',
    '2026-03-03 08:50:00'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024008'),
    'CR0008',
    'Excellent critical thinking in history essays',
    'Analyze primary sources and construct historical arguments',
    'Essays show deep understanding of historical context',
    'Strong reading comprehension, participated in debate club',
    'Independent research paper on 20th century economic history',
    'Prof. Gu',
    '2026-02-27 16:10:00'
  );

INSERT OR IGNORE INTO learning_sessions (
  student_id,
  session_code,
  session_type,
  department,
  teacher_name,
  session_time,
  summary,
  notes
) VALUES
  (
    (SELECT id FROM students WHERE student_code = 'S2024001'),
    'LS0001',
    'tutorial',
    'Mathematics',
    'Prof. Wang',
    '2026-02-18 09:10:00',
    'One-on-one tutorial on integration by parts',
    'Student benefits from visual explanations and step-by-step walkthroughs'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024002'),
    'LS0002',
    'tutorial',
    'Mathematics',
    'Prof. Zhou',
    '2026-01-12 13:40:00',
    'Review session on matrix operations and determinants',
    'Recommend daily practice of 3-5 problems to build fluency'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024003'),
    'LS0003',
    'lab',
    'Computer Science',
    'Prof. Chen',
    '2026-03-01 09:50:00',
    'Advanced data structures lab: binary trees and heaps',
    'Student completed all exercises including bonus challenge'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024004'),
    'LS0004',
    'tutorial',
    'English',
    'Prof. Xu',
    '2026-02-05 10:55:00',
    'Essay structure workshop: thesis statements and topic sentences',
    'Significant improvement in paragraph organization observed'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024005'),
    'LS0005',
    'lab',
    'Physics',
    'Prof. Zheng',
    '2026-02-22 15:10:00',
    'Rotational motion lab: moment of inertia measurements',
    'Data collection was thorough, analysis section needs more detail'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024006'),
    'LS0006',
    'lab',
    'Chemistry',
    'Prof. Huang',
    '2026-03-08 09:20:00',
    'Organic synthesis lab: preparation of aspirin',
    'Excellent lab technique, yield was 92% with high purity'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024007'),
    'LS0007',
    'tutorial',
    'Statistics',
    'Prof. Song',
    '2026-03-03 08:25:00',
    'Introduction to hypothesis testing with real-world examples',
    'Student responds well to concrete data examples over abstract theory'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024008'),
    'LS0008',
    'seminar',
    'History',
    'Prof. Gu',
    '2026-02-27 15:45:00',
    'Group discussion on industrial revolution primary sources',
    'Outstanding contribution to class discussion, well-prepared'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024003'),
    'LS0009',
    'lecture',
    'Computer Science',
    'Prof. Chen',
    '2026-03-06 10:40:00',
    'Guest lecture: software engineering best practices',
    'Student asked insightful questions about CI/CD pipelines'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024001'),
    'LS0010',
    'exam',
    'Mathematics',
    'Prof. Wang',
    '2026-03-10 13:50:00',
    'Midterm examination: Calculus II',
    'Completed all sections, flagged two problems for partial credit review'
  ),
  (
    (SELECT id FROM students WHERE student_code = 'S2024001'),
    'LS0011',
    'tutorial',
    'Mathematics',
    'Prof. Liu',
    '2026-03-14 08:40:00',
    'Post-exam review and feedback session',
    'Identified areas for improvement: improper integrals and series convergence'
  );
