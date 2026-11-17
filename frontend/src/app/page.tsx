"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Cpu,
  Headphones,
  FileText,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  MessageSquare,
  ArrowRight,
  Send,
  RefreshCw,
  User,
  Bot,
  LifeBuoy,
  PlusCircle,
  FolderCheck,
  Check,
  Clock
} from "lucide-react";

const API_BASE = "http://localhost:8000/api";

interface Summary {
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  bank_balance: number;
  voucher_count: number;
}

interface TicketMessage {
  id: number;
  ticket_id: number;
  sender: string;
  sender_name: string;
  message: string;
  timestamp: string;
}

interface SupportTicket {
  id: number;
  customer_name: string;
  customer_email: string;
  subject: string;
  category: string;
  status: string;
  priority: string;
  assigned_to: string;
  created_at: string;
  updated_at: string;
  messages: TicketMessage[];
}

interface Voucher {
  id: number;
  voucher_number: number;
  date: string;
  description: string;
  status: string;
  ai_analyzed: boolean;
  lines: {
    id: number;
    account_number: number;
    description: string;
    debit: number;
    credit: number;
  }[];
}

interface Account {
  account_number: number;
  name: string;
  account_type: string;
  vat_code?: string;
  description?: string;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<"overview" | "support" | "scan" | "vouchers" | "cfo" | "accounts">("overview");

  // State
  const [summary, setSummary] = useState<Summary>({
    total_revenue: 0,
    total_expenses: 0,
    net_income: 0,
    bank_balance: 0,
    voucher_count: 0
  });
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [operatorReply, setOperatorReply] = useState("");
  const [vouchers, setVouchers] = useState<Voucher[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  
  // AI scan state
  const [rawInvoiceText, setRawInvoiceText] = useState("");
  const [aiParsing, setAiParsing] = useState(false);
  const [parsedResult, setParsedResult] = useState<any>(null);
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null);

  // CFO chat state
  const [cfoQuestion, setCfoQuestion] = useState("");
  const [cfoChatHistory, setCfoChatHistory] = useState<{ sender: "user" | "cfo"; text: string }[]>([
    {
      sender: "cfo",
      text: "Hei! Jeg er Phinx AI - din digitale CFO støttet av Llama 3.1. Hva kan jeg hjelpe deg med i regnskapet i dag?"
    }
  ]);
  const [cfoLoading, setCfoLoading] = useState(false);

  // Load Initial Data
  const fetchData = async () => {
    try {
      const [sumRes, tickRes, vouchRes, accRes] = await Promise.all([
        fetch(`${API_BASE}/accounting/summary`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/support/tickets`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/vouchers`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/accounts`).then(r => r.json()).catch(() => [])
      ]);

      if (sumRes) setSummary(sumRes);
      if (tickRes && Array.isArray(tickRes)) {
        setTickets(tickRes);
        if (tickRes.length > 0 && !selectedTicket) {
          setSelectedTicket(tickRes[0]);
        }
      }
      if (vouchRes && Array.isArray(vouchRes)) setVouchers(vouchRes);
      if (accRes && Array.isArray(accRes)) setAccounts(accRes);
    } catch (e) {
      console.error("Feil ved henting av data:", e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  // Send Operator Reply
  const handleSendOperatorReply = async () => {
    if (!selectedTicket || !operatorReply.trim()) return;

    try {
      const res = await fetch(`${API_BASE}/support/tickets/${selectedTicket.id}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender: "OPERATOR_YOU",
          sender_name: "Deg (Kundeserviceleder)",
          message: operatorReply
        })
      });

      if (res.ok) {
        setOperatorReply("");
        fetchData();
        // Update selected ticket messages locally
        const newMsg: TicketMessage = {
          id: Date.now(),
          ticket_id: selectedTicket.id,
          sender: "OPERATOR_YOU",
          sender_name: "Deg (Kundeserviceleder)",
          message: operatorReply,
          timestamp: new Date().toISOString()
        };
        setSelectedTicket({
          ...selectedTicket,
          status: "OPERATOR_ACTIVE",
          messages: [...selectedTicket.messages, newMsg]
        });
      }
    } catch (e) {
      alert("Feil ved sending av svar: " + e);
    }
  };

  // Mark ticket as resolved
  const handleResolveTicket = async (ticketId: number) => {
    try {
      await fetch(`${API_BASE}/support/tickets/${ticketId}/status?status=RESOLVED`, {
        method: "POST"
      });
      fetchData();
      if (selectedTicket && selectedTicket.id === ticketId) {
        setSelectedTicket({ ...selectedTicket, status: "RESOLVED" });
      }
    } catch (e) {
      alert("Kunne ikke oppdatere sak: " + e);
    }
  };

  // AI Invoice Parse
  const handleParseInvoice = async () => {
    if (!rawInvoiceText.trim()) return;
    setAiParsing(true);
    setParsedResult(null);
    setBookingSuccess(null);

    try {
      const res = await fetch(`${API_BASE}/ai/parse-invoice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invoice_text: rawInvoiceText })
      });
      const data = await res.json();
      setParsedResult(data);
    } catch (e) {
      alert("Feil under AI-tolking: " + e);
    } finally {
      setAiParsing(false);
    }
  };

  // Book Parsed Voucher
  const handleBookVoucher = async () => {
    if (!parsedResult) return;

    try {
      const res = await fetch(`${API_BASE}/accounting/vouchers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: `Faktura fra ${parsedResult.supplier || "Leverandør"} (${parsedResult.kid_or_ref || "Bilag"})`,
          source_document: parsedResult.kid_or_ref || "Bilag",
          lines: parsedResult.suggested_lines
        })
      });

      if (res.ok) {
        setBookingSuccess("Bilaget ble suksessfullt bokført i hovedboken med balansert debet/kredit!");
        setParsedResult(null);
        setRawInvoiceText("");
        fetchData();
      } else {
        const err = await res.json();
        alert("Bokføringsfeil: " + (err.detail || JSON.stringify(err)));
      }
    } catch (e) {
      alert("Feil ved bokføring: " + e);
    }
  };

  // Ask CFO Chat
  const handleAskCfo = async () => {
    if (!cfoQuestion.trim() || cfoLoading) return;
    const q = cfoQuestion;
    setCfoQuestion("");
    setCfoChatHistory(prev => [...prev, { sender: "user", text: q }]);
    setCfoLoading(true);

    try {
      const res = await fetch(`${API_BASE}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q })
      });
      const data = await res.json();
      setCfoChatHistory(prev => [...prev, { sender: "cfo", text: data.reply }]);
    } catch (e) {
      setCfoChatHistory(prev => [...prev, { sender: "cfo", text: "Beklager, kunne ikke hente svar fra AI-motoren akkurat nå." }]);
    } finally {
      setCfoLoading(false);
    }
  };

  const pendingCount = tickets.filter(t => t.status === "ESCALATED_TO_HUMAN").length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 font-bold text-xl text-white">
              Φ
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-white">Phinx Accounting</h1>
                <span className="text-xs bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded-full font-medium">
                  v0.1.0 Enterprise
                </span>
              </div>
              <p className="text-xs text-slate-400">Dobbel bokføring • Llama 3.1 AI • Live Operatørdriver</p>
            </div>
          </div>

          {/* Badges */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            <div className="flex items-center space-x-1.5 bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 px-3 py-1 rounded-full shadow-sm">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>AES-256 Kryptert & Manipulasjonssikret</span>
            </div>

            <div className="flex items-center space-x-1.5 bg-indigo-950/80 border border-indigo-700/60 text-indigo-300 px-3 py-1 rounded-full shadow-sm">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>Meta Llama 3.1 AI</span>
            </div>

            <div className="flex items-center space-x-1.5 bg-amber-950/80 border border-amber-700/60 text-amber-300 px-3 py-1 rounded-full shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <Headphones className="w-3.5 h-3.5 text-amber-400" />
              <span>Operatør: Deg (Aktiv på vakt)</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 flex space-x-1 overflow-x-auto text-sm border-t border-slate-800/60 pt-1">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2.5 font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === "overview"
                ? "border-cyan-400 text-cyan-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Oversikt & Tall</span>
          </button>

          <button
            onClick={() => setActiveTab("support")}
            className={`px-4 py-2.5 font-medium border-b-2 transition flex items-center space-x-2 relative ${
              activeTab === "support"
                ? "border-cyan-400 text-cyan-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Headphones className="w-4 h-4" />
            <span>Kundeservice Desk</span>
            {pendingCount > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-red-500 text-white animate-bounce">
                {pendingCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("scan")}
            className={`px-4 py-2.5 font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === "scan"
                ? "border-cyan-400 text-cyan-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>AI Bilagsmottak</span>
          </button>

          <button
            onClick={() => setActiveTab("vouchers")}
            className={`px-4 py-2.5 font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === "vouchers"
                ? "border-cyan-400 text-cyan-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <FolderCheck className="w-4 h-4" />
            <span>Hovedbok & Bilag</span>
          </button>

          <button
            onClick={() => setActiveTab("cfo")}
            className={`px-4 py-2.5 font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === "cfo"
                ? "border-cyan-400 text-cyan-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>Llama CFO Chat</span>
          </button>

          <button
            onClick={() => setActiveTab("accounts")}
            className={`px-4 py-2.5 font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === "accounts"
                ? "border-cyan-400 text-cyan-400 bg-slate-900"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <LifeBuoy className="w-4 h-4" />
            <span>Kontoplan (NS 4102)</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">

        {/* TAB 1: OVERSIKT */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Bankinnskudd (Konto 1920)</p>
                    <h3 className="text-2xl font-bold text-white mt-1">
                      {summary.bank_balance.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} kr
                    </h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400">
                    <DollarSign className="w-6 h-6" />
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-3 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Avstemt mot hovedbok
                </p>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Driftsinntekter (3xxx)</p>
                    <h3 className="text-2xl font-bold text-emerald-400 mt-1">
                      {summary.total_revenue.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} kr
                    </h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-3">Salgsinntekter og fakturert</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Driftskostnader (4-7xxx)</p>
                    <h3 className="text-2xl font-bold text-rose-400 mt-1">
                      {summary.total_expenses.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} kr
                    </h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400">
                    <FileText className="w-6 h-6" />
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-3">Innkjøp, lisenser, drift</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Netto Driftsresultat</p>
                    <h3 className={`text-2xl font-bold mt-1 ${summary.net_income >= 0 ? "text-cyan-400" : "text-amber-400"}`}>
                      {summary.net_income.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} kr
                    </h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400">
                    <Cpu className="w-6 h-6" />
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-3">{summary.voucher_count} bokførte bilag totalt</p>
              </div>
            </div>

            {/* Quick Action Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Support desk notification banner */}
              <div className="bg-gradient-to-br from-slate-900 to-indigo-950 border border-indigo-800/40 rounded-2xl p-6 relative overflow-hidden">
                <div className="relative z-10">
                  <div className="flex items-center space-x-2 text-indigo-400 mb-2">
                    <Headphones className="w-5 h-5" />
                    <span className="font-semibold text-sm">Operatørstasjon (Kundeservice)</span>
                  </div>
                  <h4 className="text-lg font-bold text-white mb-1">
                    {pendingCount > 0 ? `${pendingCount} henvendelse(r) venter på din godkjenning!` : "Ingen ventende henvendelser akkurat nå."}
                  </h4>
                  <p className="text-sm text-slate-300 mb-4">
                    Kunder som ber om refusjon eller opplever betalingsfeil blir automatisk overført til deg her.
                  </p>
                  <button
                    onClick={() => setActiveTab("support")}
                    className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition shadow-lg shadow-indigo-600/30"
                  >
                    <span>Åpne Kundeservicedesk</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Llama 3.1 AI Banner */}
              <div className="bg-gradient-to-br from-slate-900 to-cyan-950 border border-cyan-800/40 rounded-2xl p-6">
                <div className="flex items-center space-x-2 text-cyan-400 mb-2">
                  <Cpu className="w-5 h-5" />
                  <span className="font-semibold text-sm">Meta Llama 3.1 AI Assistent</span>
                </div>
                <h4 className="text-lg font-bold text-white mb-1">Klar for bilagstolkning & finansiell rådgivning</h4>
                <p className="text-sm text-slate-300 mb-4">
                  AI-en analyserer fakturaer, foreslår debet/kredit i henhold til NS 4102 og bistår som din digitale CFO.
                </p>
                <button
                  onClick={() => setActiveTab("scan")}
                  className="inline-flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition shadow-lg shadow-cyan-600/30"
                >
                  <span>Skann faktura med AI</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: KUNDESERVICE DESK (DEG + LLAMA) */}
        {activeTab === "support" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[720px]">
            {/* Ticket List Sidebar */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white flex items-center gap-2">
                    <Headphones className="w-4 h-4 text-cyan-400" />
                    <span>Innboks Kundeservice</span>
                  </h3>
                  <p className="text-xs text-slate-400">Refusjoner, feil og henvendelser</p>
                </div>
                <button
                  onClick={fetchData}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                  title="Oppdater saker"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
                {tickets.length === 0 ? (
                  <div className="p-6 text-center text-slate-500 text-sm">Ingen henvendelser funnet.</div>
                ) : (
                  tickets.map(ticket => (
                    <div
                      key={ticket.id}
                      onClick={() => setSelectedTicket(ticket)}
                      className={`p-4 cursor-pointer transition text-left ${
                        selectedTicket?.id === ticket.id
                          ? "bg-slate-800/80 border-l-4 border-cyan-400"
                          : "hover:bg-slate-800/40"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-sm text-white truncate">{ticket.customer_name}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                          ticket.category === "REFUND"
                            ? "bg-red-950 text-red-300 border border-red-800"
                            : ticket.category === "PAYMENT_FAILED"
                            ? "bg-amber-950 text-amber-300 border border-amber-800"
                            : "bg-blue-950 text-blue-300 border border-blue-800"
                        }`}>
                          {ticket.category}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-slate-300 truncate">{ticket.subject}</p>
                      <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1">
                          {ticket.status === "ESCALATED_TO_HUMAN" ? (
                            <span className="text-amber-400 font-semibold flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3 text-amber-400" /> Venter på deg
                            </span>
                          ) : ticket.status === "RESOLVED" ? (
                            <span className="text-emerald-400 flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" /> Løst
                            </span>
                          ) : (
                            <span className="text-cyan-400">Aktiv samtale</span>
                          )}
                        </span>
                        <span>#{ticket.id}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Ticket Conversation & Operator Panel */}
            <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
              {selectedTicket ? (
                <>
                  {/* Ticket Header */}
                  <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-900/60">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white text-base">{selectedTicket.subject}</h3>
                        <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full">
                          Sak #{selectedTicket.id}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Kunde: <span className="text-slate-200">{selectedTicket.customer_name}</span> ({selectedTicket.customer_email})
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {selectedTicket.status !== "RESOLVED" && (
                        <button
                          onClick={() => handleResolveTicket(selectedTicket.id)}
                          className="flex items-center gap-1 bg-emerald-600/20 text-emerald-400 border border-emerald-600/40 hover:bg-emerald-600/30 px-3 py-1.5 rounded-xl text-xs font-medium transition"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Marker som løst</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Messages Thread */}
                  <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-950/40">
                    {selectedTicket.messages.map(msg => {
                      const isCustomer = msg.sender === "CUSTOMER";
                      const isLlama = msg.sender === "LLAMA_AI";
                      const isOperator = msg.sender === "OPERATOR_YOU";

                      return (
                        <div
                          key={msg.id}
                          className={`flex items-start gap-3 ${isOperator ? "justify-end" : "justify-start"}`}
                        >
                          {!isOperator && (
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                              isCustomer ? "bg-slate-800 text-slate-200" : "bg-indigo-600 text-white"
                            }`}>
                              {isCustomer ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                            </div>
                          )}

                          <div className={`max-w-[80%] rounded-2xl p-4 shadow-sm text-sm ${
                            isOperator
                              ? "bg-cyan-600 text-white rounded-br-none"
                              : isLlama
                              ? "bg-indigo-950/70 border border-indigo-800/60 text-indigo-100 rounded-bl-none"
                              : "bg-slate-800 text-slate-100 rounded-bl-none"
                          }`}>
                            <div className="flex items-center justify-between gap-4 mb-1">
                              <span className="font-bold text-xs opacity-80">
                                {msg.sender_name} {isLlama && "(AI 1. linje)"} {isOperator && "(Du)"}
                              </span>
                              <span className="text-[10px] opacity-60">
                                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.message}</p>
                          </div>

                          {isOperator && (
                            <div className="w-8 h-8 rounded-full bg-cyan-600 text-white flex items-center justify-center shrink-0 font-bold text-xs">
                              Deg
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Operator Action Bar & Input */}
                  <div className="p-4 border-t border-slate-800 bg-slate-900">
                    {/* Quick action buttons for refunds and failed payments */}
                    <div className="flex flex-wrap gap-2 mb-3">
                      <button
                        onClick={() => setOperatorReply("Hei! Refusjonen på beløpet er godkjent og overført via bankkonto. Du vil se pengene på konto innen 1-2 virkedager.")}
                        className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1 rounded-lg border border-slate-700 transition"
                      >
                        ⚡ Hurtigsvar: Godkjenn refusjon
                      </button>
                      <button
                        onClick={() => setOperatorReply("Hei! Vi har sjekket systemet og ser at betalingsforespørselen feilet hos bankens gateway. Ingen penger ble trukket. Du kan trygt prøve på nytt nå.")}
                        className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1 rounded-lg border border-slate-700 transition"
                      >
                        ⚡ Hurtigsvar: Avklar betalingsfeil
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <textarea
                        value={operatorReply}
                        onChange={(e) => setOperatorReply(e.target.value)}
                        placeholder="Skriv svar direkte til kunden som kundeserviceleder..."
                        rows={2}
                        className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 resize-none"
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSendOperatorReply();
                          }
                        }}
                      />
                      <button
                        onClick={handleSendOperatorReply}
                        disabled={!operatorReply.trim()}
                        className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-5 py-3 rounded-xl font-medium transition flex items-center justify-center shrink-0 shadow-lg shadow-cyan-600/20"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500 p-8 text-center">
                  <Headphones className="w-12 h-12 text-slate-600 mb-3" />
                  <p className="font-medium text-slate-400">Velg en sak fra innboksen til venstre for å svare kunden.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: AI BILAGSMOTTAK */}
        {activeTab === "scan" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Box */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div>
                <h3 className="font-bold text-white text-lg flex items-center gap-2">
                  <FileText className="w-5 h-5 text-cyan-400" />
                  <span>AI Fakturatolk & Bilagsmottak</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Lim inn fakturatekst eller kvittering. Llama 3.1 tolker beløp, MVA og foreslår balanserte kontoer.
                </p>
              </div>

              <textarea
                value={rawInvoiceText}
                onChange={(e) => setRawInvoiceText(e.target.value)}
                rows={9}
                placeholder="Lim inn tekst fra faktura eller kvittering her, f.eks.:&#10;&#10;GitHub Enterprise / Microsoft Azure&#10;Fakturanr: 2026-9912&#10;Dato: 17.11.2026&#10;Sum ekskl. mva: kr 1 200,00&#10;MVA 25%: kr 300,00&#10;Totalsum: kr 1 500,00&#10;KID: 00987654321"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setRawInvoiceText(
                    "Faktura fra WebHosting Norge AS\nFakturanummer: 88412\nDato: 17.11.2026\nForfallsdato: 01.12.2026\nBeskrivelse: Skylisenser og hosting for Q4\nBeløp: 4 500,00 NOK\nHerav 25% MVA: 900,00 NOK\nKID: 000123456789"
                  )}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition"
                >
                  Eksempel 1: Skylisenser (6540)
                </button>
                <button
                  onClick={() => setRawInvoiceText(
                    "KONTORLAND NORGE\nKvittering: 55104\nDato: 17.11.2026\nKjøp av kontorrekvisita og papir\nSum å betale: 850,00 NOK\nKortbetaling Bank"
                  )}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition"
                >
                  Eksempel 2: Kontorrekvisita (6800)
                </button>
              </div>

              <button
                onClick={handleParseInvoice}
                disabled={aiParsing || !rawInvoiceText.trim()}
                className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white py-3 rounded-xl font-medium transition flex items-center justify-center space-x-2 shadow-lg shadow-cyan-600/25"
              >
                {aiParsing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Llama 3.1 analyserer bilag...</span>
                  </>
                ) : (
                  <>
                    <Cpu className="w-4 h-4" />
                    <span>Analyser bilag med Llama AI</span>
                  </>
                )}
              </button>

              {bookingSuccess && (
                <div className="p-4 rounded-xl bg-emerald-950/80 border border-emerald-700/60 text-emerald-200 text-sm flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
                  <span>{bookingSuccess}</span>
                </div>
              )}
            </div>

            {/* AI Proposal Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-white text-lg flex items-center gap-2 mb-4">
                  <Bot className="w-5 h-5 text-indigo-400" />
                  <span>AI Forslag til Bokføring (NS 4102)</span>
                </h3>

                {parsedResult ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                        <span className="text-slate-400 block">Leverandør</span>
                        <span className="text-white font-bold text-sm">{parsedResult.supplier || "Ukjent"}</span>
                      </div>
                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                        <span className="text-slate-400 block">Totalbeløp</span>
                        <span className="text-cyan-400 font-bold text-sm">{parsedResult.total_amount?.toLocaleString("nb-NO")} kr</span>
                      </div>
                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                        <span className="text-slate-400 block">Foreslått konto</span>
                        <span className="text-white font-bold">{parsedResult.suggested_expense_account} - {parsedResult.account_name}</span>
                      </div>
                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                        <span className="text-slate-400 block">KID / Ref</span>
                        <span className="text-white font-mono">{parsedResult.kid_or_ref || "Ingen"}</span>
                      </div>
                    </div>

                    <div className="bg-indigo-950/40 border border-indigo-900/60 p-3 rounded-xl text-xs text-indigo-200">
                      <p className="font-semibold mb-1">AI-begrunnelse:</p>
                      <p>{parsedResult.explanation}</p>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        Balanserte konteringslinjer (Debet / Kredit):
                      </h4>
                      <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden divide-y divide-slate-800 text-xs">
                        {parsedResult.suggested_lines?.map((line: any, idx: number) => (
                          <div key={idx} className="p-3 flex items-center justify-between">
                            <div>
                              <span className="font-bold text-white mr-2">Konto {line.account_number}</span>
                              <span className="text-slate-400">{line.description}</span>
                            </div>
                            <div className="text-right font-mono">
                              {line.debit > 0 ? (
                                <span className="text-emerald-400 font-bold">Debet: {line.debit.toLocaleString("nb-NO")} kr</span>
                              ) : (
                                <span className="text-amber-400 font-bold">Kredit: {line.credit.toLocaleString("nb-NO")} kr</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-center">
                    <FileText className="w-10 h-10 text-slate-700 mb-2" />
                    <p className="text-sm">Lim inn fakturatekst til venstre og klikk på Analyser for å generere et balansert bilag.</p>
                  </div>
                )}
              </div>

              {parsedResult && (
                <button
                  onClick={handleBookVoucher}
                  className="mt-6 w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-medium transition flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/25"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Godkjenn & Bokfør i Hovedbok</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: HOVEDBOK & BILAG */}
        {activeTab === "vouchers" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-lg">Hovedbok & Bokførte Bilag</h3>
                <p className="text-xs text-slate-400">Revisjonssikret journal (Append-only). Ubalanserte bilag avvises automatisk.</p>
              </div>
              <div className="text-xs bg-slate-800 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">
                Totalt: <span className="font-bold text-white">{vouchers.length} bilag</span>
              </div>
            </div>

            <div className="divide-y divide-slate-800/80 overflow-x-auto">
              {vouchers.length === 0 ? (
                <div className="p-12 text-center text-slate-500 text-sm">
                  Ingen bilag er bokført enda. Gå til «AI Bilagsmottak» for å registrere det første bilaget!
                </div>
              ) : (
                vouchers.map(v => (
                  <div key={v.id} className="p-5 hover:bg-slate-800/30 transition">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                      <div className="flex items-center space-x-3">
                        <span className="px-2.5 py-1 bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono text-xs font-bold rounded-lg">
                          Bilag #{v.voucher_number}
                        </span>
                        <h4 className="font-semibold text-white text-sm">{v.description}</h4>
                      </div>
                      <div className="flex items-center space-x-3 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {new Date(v.date).toLocaleDateString("nb-NO")}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-medium text-[10px]">
                          POSTED (LÅST)
                        </span>
                      </div>
                    </div>

                    {/* Transaction lines */}
                    <div className="bg-slate-950 rounded-xl border border-slate-800/80 p-3 space-y-2 text-xs">
                      {v.lines.map(line => (
                        <div key={line.id} className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-mono font-bold text-slate-300">Konto {line.account_number}</span>
                            <span className="text-slate-400">- {line.description}</span>
                          </div>
                          <div className="font-mono">
                            {line.debit > 0 ? (
                              <span className="text-emerald-400 font-semibold">Debet: {line.debit.toLocaleString("nb-NO")} kr</span>
                            ) : (
                              <span className="text-rose-400 font-semibold">Kredit: {line.credit.toLocaleString("nb-NO")} kr</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 5: LLAMA CFO CHAT */}
        {activeTab === "cfo" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[650px] overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Phinx AI - Digital CFO</h3>
                  <p className="text-xs text-slate-400">Koblet mot sanntidstall fra regnskapet ditt</p>
                </div>
              </div>
              <span className="text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-1 rounded-full">
                Meta Llama 3.1 Powered
              </span>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-950/40">
              {cfoChatHistory.map((item, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 ${item.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  {item.sender === "cfo" && (
                    <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div className={`max-w-[80%] rounded-2xl p-4 text-sm ${
                    item.sender === "user"
                      ? "bg-cyan-600 text-white rounded-br-none"
                      : "bg-slate-800 text-slate-100 rounded-bl-none border border-slate-700/60"
                  }`}>
                    <p className="whitespace-pre-wrap leading-relaxed">{item.text}</p>
                  </div>

                  {item.sender === "user" && (
                    <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center text-white shrink-0 font-bold text-xs">
                      Du
                    </div>
                  )}
                </div>
              ))}
              {cfoLoading && (
                <div className="flex items-center space-x-2 text-xs text-slate-400 p-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                  <span>Llama 3.1 tenker og regner...</span>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t border-slate-800 bg-slate-900">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={cfoQuestion}
                  onChange={(e) => setCfoQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAskCfo()}
                  placeholder="Spør AI om driftsresultat, likviditet, skatt eller regnskapsregler..."
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500"
                />
                <button
                  onClick={handleAskCfo}
                  disabled={cfoLoading || !cfoQuestion.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-5 py-3 rounded-xl font-medium transition flex items-center justify-center shrink-0 shadow-lg shadow-indigo-600/20"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: KONTOPLAN (NS 4102) */}
        {activeTab === "accounts" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-lg">Norsk Standard Kontoplan (NS 4102)</h3>
                <p className="text-xs text-slate-400">Kontoklasser tilpasset Norsk Bokføringslov og SAF-T standard.</p>
              </div>
            </div>

            <div className="divide-y divide-slate-800 overflow-x-auto text-sm">
              <div className="p-3 bg-slate-950 text-slate-400 font-bold text-xs uppercase grid grid-cols-12">
                <div className="col-span-2">Konto</div>
                <div className="col-span-4">Kontonavn</div>
                <div className="col-span-2">Type</div>
                <div className="col-span-2">MVA-kode</div>
                <div className="col-span-2">Beskrivelse</div>
              </div>

              {accounts.map(acc => (
                <div key={acc.account_number} className="p-3 grid grid-cols-12 items-center hover:bg-slate-800/40 transition text-xs">
                  <div className="col-span-2 font-mono font-bold text-cyan-400">{acc.account_number}</div>
                  <div className="col-span-4 font-semibold text-white">{acc.name}</div>
                  <div className="col-span-2">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      acc.account_type === "ASSET" ? "bg-blue-950 text-blue-300" :
                      acc.account_type === "LIABILITY" ? "bg-amber-950 text-amber-300" :
                      acc.account_type === "REVENUE" ? "bg-emerald-950 text-emerald-300" :
                      "bg-rose-950 text-rose-300"
                    }`}>
                      {acc.account_type}
                    </span>
                  </div>
                  <div className="col-span-2 font-mono text-slate-400">{acc.vat_code || "Ingen"}</div>
                  <div className="col-span-2 text-slate-400 truncate">{acc.description || "-"}</div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>

      {/* Footer with Legal License Notice */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <p>Phinx Accounting • Bygget med dobbel bokføring og lokal Llama 3.1 AI • Full personvernisolasjon</p>
        <p className="mt-1 text-[11px] text-slate-600">
          Llama 3.1 is licensed under the Llama 3.1 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved.
        </p>
      </footer>
    </div>
  );
}
