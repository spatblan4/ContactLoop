export function filterStudents(students, query) {
  const normalizedQuery = String(query ?? '').trim().toLowerCase();
  if (!normalizedQuery) return [...students];
  return students.filter(student => [student.name, student.parent, student.relation, student.phone]
    .some(value => String(value ?? '').toLowerCase().includes(normalizedQuery)));
}
