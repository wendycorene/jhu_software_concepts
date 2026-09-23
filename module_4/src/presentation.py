"""Question wording and presentation shared by console, PDF, and Flask."""
QUESTIONS = {
1: 'How many entries are for Fall 2026?',
2: 'Among entries with a nationality classification, what percentage are international?',
3: 'What are the average GPA, GRE Quantitative, GRE Verbal, and GRE Analytical Writing scores?',
4: 'What is the average GPA of American applicants for Fall 2026?',
5: 'What percentage of Fall 2025 entries are acceptances?',
6: 'What is the average GPA of accepted applicants for Fall 2026?',
7: "How many entries are for a Computer Science master's degree at Johns Hopkins University (original fields)?",
8: 'How many Fall 2026 acceptances are for a Computer Science PhD at Georgetown, MIT, Stanford, or Carnegie Mellon (original fields)?',
9: 'How does the Question 8 count change when using LLM-generated university and program fields?',
10: 'Which five programs have the highest average GRE Quantitative scores (at least 10 valid scores)?',
11: 'Which five universities have the most reported rejections across all terms?'
}
EXPLANATIONS = {
1: 'Count entries with the specified term, ignoring capitalization and surrounding spaces.',
2: 'Divide international entries by entries with a nonblank nationality. American and Other remain in the denominator. The source sentinel 0 is loaded as NULL.',
3: 'AVG ignores NULL separately for each metric, so an entry can contribute to one average without providing the others.',
4: 'Restrict the term and nationality, then average the available GPAs.',
5: 'Divide accepted Fall 2025 entries by all Fall 2025 entries. A zero denominator produces N/A.',
6: 'Restrict the term and admission status, then average available GPAs.',
7: 'Match Computer Science and Johns Hopkins or the JHU acronym in the original combined program field, and require a master degree variant.',
8: 'Require all five conditions: Fall 2026, acceptance, PhD, Computer Science, and one of the four named universities.',
9: 'Repeat Q8 with the standardized university and program fields; subtract the original count from the LLM count. Original term, status, and degree still control eligibility.',
10: 'Group standardized program names across all terms and universities, ignoring case and surrounding spaces. Exclude missing names and invalid GRE Quantitative scores, require at least 10 scores, and rank by average score. Alphabetical order breaks ties.',
11: 'Count rejected entries across all terms by standardized university name, ignoring case and surrounding spaces and excluding missing names. Return the five largest counts, breaking ties alphabetically. These are reported counts, not rejection rates.'
}

def decimal(value, percent=False):
    return 'N/A' if value is None else f'{value:.2f}' + ('%' if percent else '')


def format_result(question, rows, results=None):
    if question == 3:
        return '; '.join(f'{name}: {decimal(value)}' for name, value in zip(
            ('Average GPA', 'Average GRE Quantitative', 'Average GRE Verbal', 'Average GRE Analytical Writing'), rows[0]))
    if question == 9:
        original, llm = results[8][0][0], rows[0][0]
        return f'Original-field count: {original}; LLM-field count: {llm}; Difference: {llm-original:+d}'
    if question == 10:
        return '; '.join(f'{name}: {decimal(average)} ({count} scores)'
                         for name, average, count in rows) or 'N/A'
    if question == 11:
        return '; '.join(f'{name}: {count} rejections'
                         for name, count in rows) or 'N/A'
    value = rows[0][0]
    if question in (1, 7, 8):
        return str(value)
    return decimal(value, question in (2, 5))


def print_results(results):
    for number, rows in results.items():
        print(f'Q{number}. {QUESTIONS[number]}')
        print(f'Answer: {format_result(number, rows, results)}\n')
