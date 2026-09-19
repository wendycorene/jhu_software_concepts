"""All webpage reads and the six required repeat analyses use ORM expressions."""
from sqlalchemy import select, func
from models import Applicant as A, Session
from presentation import print_results


def statements():
    normalized = lambda column: func.lower(func.trim(column))
    fall = normalized(A.term) == 'fall 2026'
    accepted = normalized(A.status).in_(['accepted', 'acceptance', 'admitted'])
    phd = normalized(A.degree).in_(['phd', 'ph.d.', 'ph.d', 'doctor of philosophy'])
    masters = normalized(A.degree).in_(['masters', 'master', "master's", 'ms', 'm.s.', 'msc', 'm.sc.', 'meng', 'm.eng.'])
    nationality = normalized(A.us_or_international)
    universities = r'(georgetown|massachusetts institute of technology|\mmit\M|stanford|carnegie mellon|\mcmu\M)'
    cs = r'computer\s+science'
    count = func.count(A.p_id)
    percentage = lambda numerator: 100.0 * numerator / func.nullif(count, 0)
    return {
        1: select(count).where(fall),
        2: select(100.0 * count.filter(nationality == 'international') /
                  func.nullif(func.count(func.nullif(func.trim(A.us_or_international), '')), 0)),
        3: select(func.avg(A.gpa), func.avg(A.gre), func.avg(A.gre_v), func.avg(A.gre_aw)),
        4: select(func.avg(A.gpa)).where(fall, nationality == 'american'),
        5: select(percentage(count.filter(accepted))).where(normalized(A.term) == 'fall 2025'),
        6: select(func.avg(A.gpa)).where(fall, accepted),
        7: select(count).where(A.program.regexp_match(r'(johns hopkins|\mjhu\M)', flags='i'),
                               A.program.regexp_match(cs, flags='i'), masters),
        8: select(count).where(fall, accepted, phd, A.program.regexp_match(cs, flags='i'),
                               A.program.regexp_match(universities, flags='i')),
        9: select(count).where(fall, accepted, phd, A.llm_generated_program.regexp_match(cs, flags='i'),
                               A.llm_generated_university.regexp_match(universities, flags='i')),
        10: select(normalized(A.llm_generated_program), func.avg(A.gre), func.count(A.gre))
            .where(A.gre.between(130, 170),
                   normalized(A.llm_generated_program).not_in(['', 'unknown', 'n/a']))
            .group_by(normalized(A.llm_generated_program))
            .having(func.count(A.gre) >= 10)
            .order_by(func.avg(A.gre).desc(), normalized(A.llm_generated_program)).limit(5),
        11: select(normalized(A.llm_generated_university), count)
            .where(normalized(A.status) == 'rejected',
                   normalized(A.llm_generated_university).not_in(['', 'unknown', 'n/a']))
            .group_by(normalized(A.llm_generated_university))
            .order_by(count.desc(), normalized(A.llm_generated_university)).limit(5)
    }


def run_queries(session=None):
    def run(active):
        return {number: [tuple(row) for row in active.execute(statement)]
                for number, statement in statements().items()}
    if session is not None:
        return run(session)
    with Session() as active:
        return run(active)

if __name__ == '__main__':
    print_results(run_queries())
