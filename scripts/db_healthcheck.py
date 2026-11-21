"""Rychla kontrola: ktora DB sa pouziva, ci ma data a ci hesla sedia."""
import os, sqlite3, sys
from urllib.parse import urlparse
env = os.path.expanduser('~/KOMPAS/.env')
url = None
if os.path.exists(env):
    for line in open(env):
        if line.startswith('DATABASE_URL='):
            url = line.split('=', 1)[1].strip()
if not url:
    print('CHYBA: DATABASE_URL chyba v .env'); sys.exit(1)
path = url.replace('sqlite:///', '', 1)
if not path.startswith('/'):
    path = os.path.join(os.path.expanduser('~/KOMPAS'), path)
print('DATABASE_URL =', url)
print('Realna cesta =', path, '| existuje:', os.path.exists(path))
if not os.path.exists(path):
    sys.exit(1)
con = sqlite3.connect('file:%s?mode=ro' % path, uri=True)
print('skoly:', list(con.execute('select id, name from school_school')))
print('demo users:', [r[0] for r in con.execute("select username from identity_user where username like 'demo_%'")])
try:
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    for u, h in con.execute("select username, password_hash from identity_user where username like 'demo_%'"):
        try:
            ok = ph.verify(h, 'demo-password')
        except Exception as e:
            ok = 'NIE (%s)' % type(e).__name__
        print('  ', u, '-> heslo sedi:', ok)
except ImportError:
    print('  (argon2 nie je v systemovom Pythone, preskakujem verifikaciu hesiel)')
con.close()
