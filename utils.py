from flask import jsonify

import mydb as db

import re
from rapidfuzz import process, fuzz

def json_response(type_=None, message=None, icon=None, redirect_to=None):
    return jsonify({
        'type': type_,  # 'error', 'warning', 'info', 'success'
        'message': message,
        'icon': icon,   # пока что нет
        'redirect_to': redirect_to
    })

def search_raw(query, all_results, limit=3):
    if not query:
        return []

    direct_matches = [
        r for r in all_results
        if query.lower() in r.title.lower()
    ]

    results = direct_matches

    if len(results) < limit:
        titles = [r.title for r in all_results]
        fuzzy_matches = process.extract(query, titles, scorer=fuzz.token_set_ratio, limit=10)
        fuzzy_titles = {m[0] for m in fuzzy_matches if m[1] > 60}

        fuzz_results = [
            r for r in all_results
            if r.title in fuzzy_titles and r not in results
        ]
        results += fuzz_results

    return results[:limit]

def search(query, all_results):
    if not query:
        return ''

    direct_matches = [
        r for r in all_results
        if query.lower() in r.title.lower()
    ]

    results = direct_matches

    if len(results) < 10:
        titles = [r.title for r in all_results]
        fuzzy_matches = process.extract(query, titles, scorer=fuzz.token_set_ratio, limit=10)
        fuzzy_titles = {m[0] for m in fuzzy_matches if m[1] > 60}

        fuzz_results = [
            r for r in all_results
            if r.title in fuzzy_titles and r not in results
        ]
        results += fuzz_results

    if not results:
        return '<p>Ничего не найдено</p>'

    def highlight(text, query):
        pattern = re.escape(query)
        return re.sub(f"({pattern})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)

    html = ''.join(
        f'<a class="suggestion-item" href="/a/{r.link}">{highlight(r.title, query)}</a>'
        for r in results
    )

    return html

not_available_links = [
    'appw', 'graphs', 'edit', 'admin', 'moderation', 'collections', 'rules', 'games', 'apps'
    'porno', 'chlen', 'blyat', 'lbv'
]

def validate_link(link):
    if len(link) > 21:
        raise ValueError('Ссылка слишком длинная (максимум 21 символ)')
    if len(link) < 3:
        raise ValueError("Ссылка слишком короткая (минимум 3 символа)")
    
    if not re.fullmatch(r'^[a-z0-9]+$', link):
        raise ValueError('Ссылка может содержать только латинские буквы и цифры')

    if link in not_available_links:
        raise ValueError('Ссылка недоступна')
    
    existing_links = [game.link for game in db.get_shares_all()]
    if link in existing_links:
        raise ValueError('Ссылка уже занята')
    
    return True