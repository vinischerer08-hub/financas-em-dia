from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'apenas-para-uso-local')
app.config['DATABASE'] = os.environ.get('FINANCAS_DB', str(Path(app.instance_path) / 'financas.db'))
CATEGORIES = ['Alimentação', 'Casa', 'Educação', 'Lazer', 'Saúde', 'Transporte', 'Salário', 'Outros']


@contextmanager
def connect_db():
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    with connect_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('receita', 'despesa')),
            category TEXT NOT NULL,
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            transaction_date TEXT NOT NULL
        )''')


@app.template_filter('brl')
def brl(cents):
    value = f'{abs(cents) // 100:,}'.replace(',', '.')
    return f"{'-' if cents < 0 else ''}R$ {value},{abs(cents) % 100:02d}"


def month_or_current(value):
    try:
        parsed = datetime.strptime(value, '%Y-%m')
        if parsed.strftime('%Y-%m') == value:
            return value
    except (ValueError, TypeError):
        pass
    return date.today().strftime('%Y-%m')


def parse_transaction(form):
    description = form.get('description', '').strip()
    kind = form.get('kind', '')
    category = form.get('category', '')
    day = form.get('transaction_date', '')
    amount = form.get('amount', '').strip().replace(',', '.')
    if not description or len(description) > 100:
        raise ValueError('Informe uma descrição de até 100 caracteres.')
    if kind not in ('receita', 'despesa') or category not in CATEGORIES:
        raise ValueError('Selecione um tipo e uma categoria válidos.')
    try:
        parsed_date = date.fromisoformat(day)
        if parsed_date.isoformat() != day:
            raise ValueError
    except ValueError:
        raise ValueError('Informe uma data válida.') from None
    try:
        value = Decimal(amount)
        if not value.is_finite() or value <= 0 or value > Decimal('999999999.99') or value.as_tuple().exponent < -2:
            raise ValueError
        cents = int(value * 100)
    except (InvalidOperation, ValueError, OverflowError):
        raise ValueError('Informe um valor positivo com até duas casas decimais.') from None
    return description, kind, category, cents, day


@app.get('/')
def index():
    month = month_or_current(request.args.get('month'))
    category = request.args.get('category', '')
    if category not in CATEGORIES:
        category = ''
    with connect_db() as conn:
        rows = conn.execute('SELECT * FROM transactions WHERE substr(transaction_date, 1, 7) = ? ORDER BY transaction_date DESC, id DESC', (month,)).fetchall()
    # Os totais representam o mês inteiro; o filtro de categoria afeta apenas a lista.
    income = sum(row['amount_cents'] for row in rows if row['kind'] == 'receita')
    expense = sum(row['amount_cents'] for row in rows if row['kind'] == 'despesa')
    groups = defaultdict(int)
    for row in rows:
        if row['kind'] == 'despesa':
            groups[row['category']] += row['amount_cents']
    chart = sorted(groups.items(), key=lambda item: item[1], reverse=True)
    filtered = [row for row in rows if not category or row['category'] == category]
    return render_template('index.html', month=month, category=category, categories=CATEGORIES,
                           transactions=filtered, income=income, expense=expense,
                           balance=income-expense, chart=chart, today=date.today().isoformat())


@app.post('/transacoes')
def create():
    try:
        values = parse_transaction(request.form)
        with connect_db() as conn:
            conn.execute('INSERT INTO transactions (description, kind, category, amount_cents, transaction_date) VALUES (?, ?, ?, ?, ?)', values)
        flash('Lançamento adicionado com sucesso.', 'success')
        return redirect(url_for('index', month=values[4][:7]))
    except ValueError as error:
        flash(str(error), 'error')
        return redirect(url_for('index', month=month_or_current(request.form.get('month'))))


@app.route('/transacoes/<int:transaction_id>/editar', methods=['GET', 'POST'])
def edit(transaction_id):
    with connect_db() as conn:
        row = conn.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
    if row is None:
        abort(404)
    if request.method == 'POST':
        try:
            values = parse_transaction(request.form)
            with connect_db() as conn:
                conn.execute('UPDATE transactions SET description=?, kind=?, category=?, amount_cents=?, transaction_date=? WHERE id=?', (*values, transaction_id))
            flash('Lançamento atualizado com sucesso.', 'success')
            return redirect(url_for('index', month=values[4][:7]))
        except ValueError as error:
            flash(str(error), 'error')
    return render_template('edit.html', transaction=row, categories=CATEGORIES)


@app.post('/transacoes/<int:transaction_id>/excluir')
def delete(transaction_id):
    month = month_or_current(request.form.get('month'))
    with connect_db() as conn:
        cursor = conn.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    flash('Lançamento excluído.' if cursor.rowcount else 'Lançamento não encontrado.', 'success' if cursor.rowcount else 'error')
    return redirect(url_for('index', month=month))


init_db()

if __name__ == '__main__':
    app.run(debug=False)

