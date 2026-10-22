import { Conversation } from '@elevenlabs/client';

const $ = (id) => document.getElementById(id);
let conv = null;
let busy = false;

const setStatus = (t) => { $('status').textContent = t; };
const setOrb = (cls, label) => { $('orb').className = cls; $('orb').textContent = label; };

async function start() {
  if (conv || busy) return;
  busy = true;
  try {
    const cfg = await window.jarvis.getConfig();
    if (!cfg.backendUrl || !cfg.token) { showSetup(); return; }
    setStatus('Подключаюсь…');
    const r = await fetch(cfg.backendUrl.replace(/\/$/, '') + '/voice/session', {
      headers: { Authorization: 'Bearer ' + cfg.token },
    });
    if (!r.ok) throw new Error('Бэкенд ответил ' + r.status);
    const { signed_url, briefing } = await r.json();
    conv = await Conversation.startSession({
      signedUrl: signed_url,
      // Used by the agent's first message ({{briefing}}): today's numbers instead of a greeting.
      dynamicVariables: { briefing: briefing || 'Слушаю, Алишер. Что делаем?' },
      onModeChange: ({ mode }) => {
        if (mode === 'speaking') { setOrb('speaking', 'Говорю'); setStatus(''); }
        else { setOrb('listening', 'Слушаю'); setStatus(''); }
      },
      onDisconnect: () => { conv = null; setOrb('', 'Нажми'); },
      onError: (m) => setStatus('Ошибка: ' + m),
    });
    setOrb('listening', 'Слушаю');
  } catch (e) {
    setStatus('Не получилось: ' + e.message);
    setOrb('', 'Нажми');
  } finally { busy = false; }
}

async function stop() {
  if (!conv) return;
  const c = conv; conv = null;
  await c.endSession();
  setOrb('', 'Нажми'); setStatus('');
}

function showSetup() {
  $('main').style.display = 'none'; $('setup').style.display = 'block';
  window.jarvis.getConfig().then((c) => { $('url').value = c.backendUrl; });
}

$('orb').onclick = () => (conv ? stop() : start());
$('gear').onclick = showSetup;
$('save').onclick = async () => {
  await window.jarvis.saveConfig({ backendUrl: $('url').value.trim(), token: $('token').value });
  $('setup').style.display = 'none'; $('main').style.display = 'block';
  setStatus('Сохранено');
};
window.jarvis.onStart(start);
window.jarvis.onStop(stop);
