"""All eleven analyses expressed as executable PostgreSQL SELECT statements."""
from config import connect
from presentation import print_results

FALL = "lower(trim(term)) = 'fall 2026'"
ACCEPTED = "lower(trim(status)) IN ('accepted', 'acceptance', 'admitted')"
PHD = "lower(trim(degree)) IN ('phd', 'ph.d.', 'ph.d', 'doctor of philosophy')"
MASTERS = "lower(trim(degree)) IN ('masters', 'master', 'master''s', 'ms', 'm.s.', 'msc', 'm.sc.', 'meng', 'm.eng.')"
# PostgreSQL word boundaries prevent MIT from matching an unrelated word.
UNIVERSITIES = r'(georgetown|massachusetts institute of technology|\mmit\M|stanford|carnegie mellon|\mcmu\M)'
CS = r'computer\s+science'
Q8_FILTER = f"{FALL} AND {ACCEPTED} AND {PHD} AND program ~* '{CS}' AND program ~* '{UNIVERSITIES}'"
Q9_FILTER = f"{FALL} AND {ACCEPTED} AND {PHD} AND llm_generated_program ~* '{CS}' AND llm_generated_university ~* '{UNIVERSITIES}'"
QUERIES = {
1: f'SELECT COUNT(*) FROM applicants WHERE {FALL}',
2: """SELECT 100.0 * COUNT(*) FILTER (WHERE lower(trim(us_or_international)) = 'international')
 / NULLIF(COUNT(NULLIF(trim(us_or_international), '')), 0) FROM applicants""",
3: 'SELECT AVG(gpa), AVG(gre), AVG(gre_v), AVG(gre_aw) FROM applicants',
4: f"SELECT AVG(gpa) FROM applicants WHERE {FALL} AND lower(trim(us_or_international)) = 'american'",
5: f"SELECT 100.0 * COUNT(*) FILTER (WHERE {ACCEPTED}) / NULLIF(COUNT(*), 0) FROM applicants WHERE lower(trim(term)) = 'fall 2025'",
6: f'SELECT AVG(gpa) FROM applicants WHERE {FALL} AND {ACCEPTED}',
7: rf"SELECT COUNT(*) FROM applicants WHERE program ~* '(johns hopkins|\mjhu\M)' AND program ~* '{CS}' AND {MASTERS}",
8: f'SELECT COUNT(*) FROM applicants WHERE {Q8_FILTER}',
9: f'SELECT COUNT(*) FROM applicants WHERE {Q9_FILTER}',
# Group across all terms; break ties alphabetically for a consistent top five.
10: """SELECT lower(trim(llm_generated_program)) AS program,
 AVG(gre) AS average_gre, COUNT(gre) AS score_count
 FROM applicants
 WHERE gre BETWEEN 130 AND 170
 AND lower(trim(llm_generated_program)) NOT IN ('', 'unknown', 'n/a')
 GROUP BY lower(trim(llm_generated_program))
 HAVING COUNT(gre) >= 10
 ORDER BY average_gre DESC, program ASC LIMIT 5""",
11: """SELECT lower(trim(llm_generated_university)) AS university,
 COUNT(*) AS rejection_count FROM applicants
 WHERE lower(trim(status)) = 'rejected'
 AND lower(trim(llm_generated_university)) NOT IN ('', 'unknown', 'n/a')
 GROUP BY lower(trim(llm_generated_university))
 ORDER BY rejection_count DESC, university ASC LIMIT 5"""
}

def run_queries(connection=None):
    def run(conn):
        with conn.cursor() as cursor:
            results = {}
            for number, sql in QUERIES.items():
                cursor.execute(sql)
                results[number] = cursor.fetchall()
            return results
    if connection is not None:
        return run(connection)
    with connect() as conn:
        return run(conn)

if __name__ == '__main__':
    print_results(run_queries())
