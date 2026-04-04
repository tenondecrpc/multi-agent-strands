import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CheckCircle, Loader2, FileText, AlertCircle } from 'lucide-react';
import type { AgentLog } from '@/types/agent';
import { cn } from '@/lib/utils';
import { useScrollToBottom } from '@/hooks/useScrollToBottom';

const TOOL_LABELS: Record<string, string> = {
  jira_get_issue: 'Fetching Jira ticket details',
  jira_transition_issue: 'Updating Jira ticket status',
  jira_add_comment: 'Adding comment to Jira',
  qa_agent: 'Running QA Agent tests',
  orchestrator: 'Running Orchestrator Agent',
  frontend_agent: 'Running Frontend Agent',
  backend_agent: 'Running Backend Agent'
};

function parsePythonDictStr(str: string) {
  try {
    // 1. Python DB format: {"tool_name": "xyz", "status": "completed"}
    const toolMatchDb = str.match(/\{\s*'tool_name':\s*'([^']+)',\s*'status':\s*'([^']+)'\s*\}/);
    if (toolMatchDb) return { type: 'tool', name: toolMatchDb[1], status: toolMatchDb[2] };

    // 2. Live WebSocket format: "Tool call: xyz" or "Tool result: xyz (completed)"
    const toolCallLive = str.match(/^Tool call:\s*(.+)$/);
    if (toolCallLive) return { type: 'tool', name: toolCallLive[1], status: 'started' };

    const toolResultLive = str.match(/^Tool result:\s*([^\s]+)(?:\s+\((.+)\))?$/);
    if (toolResultLive) return { type: 'tool', name: toolResultLive[1], status: toolResultLive[2] || 'completed' };

    // 3. Ticket started string match
    const ticketMatch = str.match(/\{\s*'ticket_id':\s*'([^']+)'\s*\}/);
    if (ticketMatch) return { type: 'ticket', id: ticketMatch[1] };

    // 4. Final result markdown extraction
    const resultMatch = str.match(/\{\s*'result':\s*'([\s\S]+?)'\s*\}/);
    if (resultMatch) {
      const resStr = resultMatch[1].replace(/\\n/g, '\n').replace(/\\'/g, "'");
      return { type: 'result', content: resStr };
    }

    return null;
  } catch {
    return null;
  }
}

interface ParsedEvent {
  id: string;
  name: string;
  label: string;
  status: 'started' | 'completed' | 'error';
  timestamp: string;
  duration?: number;
}

interface ProcessedLogs {
  ticketId: string | null;
  events: ParsedEvent[];
  finalResult: string | null;
  rawLogs: AgentLog[];
}

export const AgentLogsTimeline = ({ logs }: { logs: AgentLog[] }) => {
  const logsEndRef = useScrollToBottom<HTMLDivElement>([logs]);

  const startTime = useMemo(() => {
    const firstLog = logs[0];
    return firstLog?.timestamp || new Date().toISOString();
  }, [logs]);

  const processed = useMemo<ProcessedLogs>(() => {
    let ticketId: string | null = null;
    let finalResult: string | null = null;
    const eventsMap = new Map<string, { event: ParsedEvent; startedLogId: string | null; completedLogId: string | null }>();
    const rawLogs: AgentLog[] = [];

    // First pass: collect all tool events into the map (handles any order)
    logs.forEach(log => {
      const parsed = parsePythonDictStr(log.message);

      if (parsed) {
        if (parsed.type === 'ticket') {
          ticketId = parsed.id || null;
        } else if (parsed.type === 'result') {
          finalResult = parsed.content || null;
        } else if (parsed.type === 'tool') {
          const name = parsed.name;
          const status = parsed.status;
          if (!name) return;
          const existing = eventsMap.get(name);

          if (status === 'started') {
            if (existing) {
              existing.startedLogId = log.id;
              existing.event.timestamp = log.timestamp;
            } else {
              const newEvent: ParsedEvent = {
                id: log.id,
                name,
                label: TOOL_LABELS[name] || name,
                status: 'started',
                timestamp: log.timestamp,
              };
              eventsMap.set(name, { event: newEvent, startedLogId: log.id, completedLogId: null });
            }
          } else if (status === 'completed') {
            if (existing) {
              existing.event.status = 'completed';
              existing.completedLogId = log.id;
              const start = new Date(existing.event.timestamp).getTime();
              const end = new Date(log.timestamp).getTime();
              existing.event.duration = Math.max(0, Math.round((end - start) / 1000));
            } else {
              const newEvent: ParsedEvent = {
                id: log.id,
                name,
                label: TOOL_LABELS[name] || name,
                status: 'completed',
                timestamp: log.timestamp,
              };
              eventsMap.set(name, { event: newEvent, startedLogId: null, completedLogId: log.id });
            }
          }
        }
      } else {
        rawLogs.push(log);
      }
    });

    // Second pass: build ordered list sorted by timestamp
    const orderedEvents = Array.from(eventsMap.values())
      .map(entry => entry.event)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

    return { ticketId, events: orderedEvents, finalResult, rawLogs };
  }, [logs]);

  if (logs.length === 0) {
    return (
      <div className="py-8 text-center text-zinc-600">
        No logs yet. Waiting for stream...
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-6 px-4 py-4 text-sm font-mono text-zinc-300">
      {/* 1. Header / Intro */}
      {processed.ticketId && (
        <div className="flex items-center text-zinc-400 gap-2 mb-2 flex-nowrap">
          <span className="text-zinc-500 shrink-0">[{new Date(startTime).toLocaleTimeString('en-US', { hour12: false })}]</span>
          <span className="shrink-0">🤖 Orchestrator Agent started processing ticket</span>
          <span className="font-bold text-zinc-200 whitespace-nowrap">{processed.ticketId}</span>
        </div>
      )}

      {/* 2. Timeline Events */}
      {processed.events.length > 0 && (
        <div className="space-y-3 border-l-2 border-zinc-800 ml-4 pl-5 relative">
          {processed.events.map((event) => (
            <div key={event.id} className="flex items-center space-x-3 group relative">
              <div className="absolute -left-[27px] bg-zinc-950 rounded-full p-0.5">
                {event.status === 'started' ? (
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                ) : event.status === 'completed' ? (
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
              </div>
              
              <span className={cn(
                "transition-colors",
                event.status === 'started' ? 'text-blue-400 font-medium' : 'text-zinc-400'
              )}>
                {event.label} <span className="text-zinc-600 text-xs ml-1">({event.name})</span>
              </span>
              
              {event.duration !== undefined && (
                <span className="text-zinc-600 text-xs">[{event.duration}s]</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 3. Raw Non-Parsed Logs */}
      {processed.rawLogs.length > 0 && (
        <div className="mt-4 space-y-1">
          {processed.rawLogs.map((log) => (
            <div key={log.id} className="flex items-start gap-2 rounded-sm px-2 py-1 leading-snug break-words opacity-70 hover:opacity-100 transition-opacity">
              <span className="log-time shrink-0 text-zinc-600">
                {new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })}
              </span>
              <span className="log-agent shrink-0 text-zinc-500 font-bold">
                [{log.agent_id}]
              </span>
              <span className="log-message flex-1 text-zinc-400">
                {log.message}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* 4. Final Result (Markdown) */}
      {processed.finalResult && (
        <div className="mt-8 p-5 bg-zinc-900/60 rounded-lg border border-zinc-800 shadow-inner">
          <div className="flex items-center gap-2 mb-4 border-b border-zinc-800/80 pb-3">
            <FileText className="w-5 h-5 text-indigo-400" />
            <h3 className="text-indigo-300 font-semibold font-sans text-base">Execution Result</h3>
          </div>
          
          <div className="prose prose-invert prose-sm max-w-none font-sans prose-pre:bg-zinc-950 prose-pre:border prose-pre:border-zinc-800 prose-th:bg-zinc-900/50 prose-td:border-zinc-800 prose-th:border-zinc-800 prose-table:my-2 prose-td:px-3 prose-td:py-1.5 prose-th:px-3 prose-th:py-1.5 prose-p:my-1 prose-li:my-0.5 prose-h3:mt-4 prose-h3:mb-2 prose-h4:mt-3 prose-h4:mb-1 prose-code:text-indigo-300 prose-code:bg-zinc-800/50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {processed.finalResult}
            </ReactMarkdown>
          </div>
        </div>
      )}

      <div ref={logsEndRef} />
    </div>
  );
};
