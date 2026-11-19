"use client";

import React, { useState, useEffect, useRef } from "react";
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
  PlusCircle,
  FolderCheck,
  Check,
  Clock,
  Landmark,
  Building2,
  Users,
  Receipt,
  FileSpreadsheet,
  Settings,
  Sparkles,
  Upload,
  Eye,
  Trash2,
  Search,
  ExternalLink,
  ChevronRight,
  FileCheck,
  Calendar,
  CreditCard,
  Briefcase,
  HelpCircle,
  Download,
  X,
  FileUp,
  Bell
} from "lucide-react";
import AuthModal, { type AuthUser } from "@/components/AuthModal";
import PayrollPanel from "@/components/PayrollPanel";
import ArchiveSaftCompliancePanel from "@/components/ArchiveSaftCompliancePanel";
import NotificationsPanel from "@/components/NotificationsPanel";
import BillingPanel from "@/components/BillingPanel";
import LogoSplash from "@/components/LogoSplash";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

// --- TYPES ---
interface Summary {
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  bank_balance: number;
  voucher_count: number;
  total_receivables?: number;
  total_payables?: number;
  pending_reconciliations?: number;
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

interface VoucherLine {
  id?: number;
  account_number: number;
  description: string;
  debit: number;
  credit: number;
}

interface Voucher {
  id: number;
  voucher_number: number;
  date: string;
  description: string;
  source_document?: string;
  status: string;
  ai_analyzed: boolean;
  lines: VoucherLine[];
}

interface Account {
  account_number: number;
  name: string;
  account_type: string;
  vat_code?: string;
  description?: string;
}

interface Supplier {
  id: number;
  name: string;
  org_number?: string;
  account_number?: string;
  kid_prefix?: string;
  email?: string;
  phone?: string;
  default_expense_account: number;
  payment_terms_days: number;
  outstanding_balance: number;
  invoice_count: number;
}

interface SupplierInvoice {
  id: number;
  supplier_id: number;
  supplier_name: string;
  invoice_number: string;
  kid?: string;
  issue_date: string;
  due_date: string;
  amount_ex_vat: number;
  vat_amount: number;
  total_amount: number;
  expense_account: number;
  status: "UNPAID" | "PAID" | "OVERDUE";
  voucher_id?: number;
  attachment_url?: string;
}

interface Customer {
  id: number;
  name: string;
  org_number?: string;
  email?: string;
  phone?: string;
  address?: string;
  payment_terms_days: number;
  outstanding_balance: number;
  invoice_count: number;
}

interface InvoiceLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  vat_percent: number;
  amount: number;
}

interface CustomerInvoice {
  id: number;
  invoice_number: number;
  customer_id?: number;
  customer_name: string;
  customer_email?: string;
  customer_orgnr?: string;
  issue_date: string;
  due_date: string;
  kid?: string;
  subtotal: number;
  vat_amount: number;
  total_amount: number;
  lines: InvoiceLineItem[];
  status: string;
  voucher_id?: number;
}

interface BankTransaction {
  id: number;
  transaction_date: string;
  description: string;
  amount: number;
  reference?: string;
  reconciled: boolean;
  matched_voucher_id?: number;
  reconciled_at?: string;
  source: string;
}

interface BankSummary {
  bank_statement_balance: number;
  account_1920_balance: number;
  difference: number;
  reconciled_count: number;
  unreconciled_count: number;
  is_balanced: boolean;
}

interface UploadedDoc {
  id: number;
  filename: string;
  original_name: string;
  file_type: string;
  file_path: string;
  file_size: number;
  status: string;
  extracted_data?: any;
  voucher_id?: number;
  uploaded_at: string;
}

interface VatReportTerm {
  term: number;
  term_name: string;
  base_sales_high_25: number;
  output_vat_25: number;
  input_vat_deductible: number;
  net_vat_payable: number;
  is_settled: boolean;
}

interface CompanySettings {
  company_name: string;
  org_number: string;
  bank_account: string;
  vat_registered: boolean;
  address: string;
  postal_code: string;
  city: string;
  email: string;
  phone: string;
}

type TabType =
  | "overview"
  | "notifications"
  | "inbox"
  | "record"
  | "vouchers"
  | "archive"
  | "bank"
  | "invoices"
  | "suppliers"
  | "payroll"
  | "billing"
  | "vat"
  | "altinn"
  | "saft"
  | "compliance"
  | "reports"
  | "accounts"
  | "cfo"
  | "support"
  | "settings";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);

  useEffect(() => {
    setVoucherDate(new Date().toISOString().split("T")[0]);
    setInvDueDate(new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0]);
    fetch(`${API_BASE}/accounting/notifications`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (typeof d?.total === "number") setNotificationCount(d.total);
      })
      .catch(() => undefined);
    const token = typeof window !== "undefined" ? localStorage.getItem("phink_token") : null;
    if (!token) return;
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.ok && d.user) setCurrentUser(d.user);
      })
      .catch(() => undefined);
  }, []);

  // Core Data
  const [summary, setSummary] = useState<Summary>({
    total_revenue: 0,
    total_expenses: 0,
    net_income: 0,
    bank_balance: 0,
    voucher_count: 0,
    total_receivables: 0,
    total_payables: 0,
    pending_reconciliations: 0
  });

  const [vouchers, setVouchers] = useState<Voucher[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [supplierInvoices, setSupplierInvoices] = useState<SupplierInvoice[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [invoices, setInvoices] = useState<CustomerInvoice[]>([]);
  const [bankTransactions, setBankTransactions] = useState<BankTransaction[]>([]);
  const [bankSummary, setBankSummary] = useState<BankSummary | null>(null);
  const [documents, setDocuments] = useState<UploadedDoc[]>([]);
  const [vatReports, setVatReports] = useState<VatReportTerm[]>([]);
  const [companySettings, setCompanySettings] = useState<CompanySettings>({
    company_name: "Nordic Tech Solutions AS",
    org_number: "987 654 321 MVA",
    bank_account: "1503.22.88991",
    vat_registered: true,
    address: "Dronning Eufemias gate 16",
    postal_code: "0191",
    city: "Oslo",
    email: "post@nordictech.no",
    phone: "+47 21 55 40 00"
  });

  // Support State
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [operatorReply, setOperatorReply] = useState("");

  // CFO Chat State
  const [cfoQuestion, setCfoQuestion] = useState("");
  const [cfoChatHistory, setCfoChatHistory] = useState<{ sender: "user" | "cfo"; text: string }[]>([
    {
      sender: "cfo",
      text: "Hei! Jeg er Phink AI - din digitale CFO støttet av Llama 3.1. Hva kan jeg hjelpe deg med i regnskapet i dag?"
    }
  ]);
  const [cfoLoading, setCfoLoading] = useState(false);

  // Modal / Preview state
  const [previewFileUrl, setPreviewFileUrl] = useState<string | null>(null);
  const [previewFileType, setPreviewFileType] = useState<"image" | "pdf">("image");
  const [selectedVoucherForDetail, setSelectedVoucherForDetail] = useState<Voucher | null>(null);

  // New Voucher Booking Wizard State
  const [recordMode, setRecordMode] = useState<"purchase" | "sale" | "free">("purchase");
  const [voucherDesc, setVoucherDesc] = useState("");
  const [voucherDate, setVoucherDate] = useState("2026-11-19");
  const [purchaseAmount, setPurchaseAmount] = useState("");
  const [purchaseVat, setPurchaseVat] = useState("25");
  const [purchaseAccount, setPurchaseAccount] = useState(6540);
  const [purchaseSupplier, setPurchaseSupplier] = useState("");
  const [purchasePaymentMethod, setPurchasePaymentMethod] = useState<"bank" | "supplier_credit">("bank");
  const [attachedDocUrl, setAttachedDocUrl] = useState<string | null>(null);

  // Free Voucher Lines
  const [freeLines, setFreeLines] = useState<VoucherLine[]>([
    { account_number: 6800, description: "Kostnad", debit: 1000, credit: 0 },
    { account_number: 1920, description: "Betalt fra bank", debit: 0, credit: 1000 }
  ]);

  // New Customer Invoice Modal
  const [showNewInvoiceModal, setShowNewInvoiceModal] = useState(false);
  const [invCustomerName, setInvCustomerName] = useState("");
  const [invCustomerEmail, setInvCustomerEmail] = useState("");
  const [invDueDate, setInvDueDate] = useState("2026-12-03");
  const [invLines, setInvLines] = useState<InvoiceLineItem[]>([
    { description: "Konsulenttjenester / Lisens", quantity: 1, unit_price: 15000, vat_percent: 25, amount: 15000 }
  ]);

  // New Supplier Modal
  const [showNewSupplierModal, setShowNewSupplierModal] = useState(false);
  const [newSupName, setNewSupName] = useState("");
  const [newSupOrgnr, setNewSupOrgnr] = useState("");
  const [newSupAccount, setNewSupAccount] = useState(6540);
  const [newSupBankAcc, setNewSupBankAcc] = useState("");

  // Upload Status
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccessMsg, setUploadSuccessMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Altinn & Brreg State
  const [altinnReceipt, setAltinnReceipt] = useState<any>(null);
  const [altinnSubmitting, setAltinnSubmitting] = useState(false);
  const [brregQuery, setBrregQuery] = useState("");
  const [brregResults, setBrregResults] = useState<any[]>([]);
  const [brregSearching, setBrregSearching] = useState(false);

  // Load All Data
  const fetchAllData = async () => {
    try {
      const [
        sumRes,
        vouchRes,
        accRes,
        supRes,
        supInvRes,
        custRes,
        invRes,
        bankTxRes,
        bankSumRes,
        docRes,
        vatRes,
        settRes,
        tickRes
      ] = await Promise.all([
        fetch(`${API_BASE}/accounting/summary`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/accounting/vouchers`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/accounts`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/suppliers`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/supplier-invoices`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/customers`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/invoices`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/bank/transactions`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/bank/summary`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/accounting/documents`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/vat/report`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/accounting/settings`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/support/tickets`).then(r => r.json()).catch(() => [])
      ]);

      if (sumRes) setSummary(sumRes);
      if (Array.isArray(vouchRes)) setVouchers(vouchRes);
      if (Array.isArray(accRes)) setAccounts(accRes);
      if (Array.isArray(supRes)) setSuppliers(supRes);
      if (Array.isArray(supInvRes)) setSupplierInvoices(supInvRes);
      if (Array.isArray(custRes)) setCustomers(custRes);
      if (Array.isArray(invRes)) setInvoices(invRes);
      if (Array.isArray(bankTxRes)) setBankTransactions(bankTxRes);
      if (bankSumRes) setBankSummary(bankSumRes);
      if (Array.isArray(docRes)) setDocuments(docRes);
      if (Array.isArray(vatRes)) setVatReports(vatRes);
      if (settRes && settRes.company_name) setCompanySettings(settRes);
      if (Array.isArray(tickRes)) {
        setTickets(tickRes);
        if (tickRes.length > 0 && !selectedTicket) {
          setSelectedTicket(tickRes[0]);
        }
      }
    } catch (e) {
      console.error("Feil ved datahenting:", e);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 8000);
    return () => clearInterval(interval);
  }, []);

  // --- ACTIONS ---

  // 1. Filopplasting (Både PDF og Bilde)
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadLoading(true);
    setUploadSuccessMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/accounting/documents/upload`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Kunne ikke laste opp fil.");
      }
      const data: UploadedDoc = await res.json();
      setUploadSuccessMsg(`Bilag "${file.name}" lastet opp til innboksen!`);
      fetchAllData();

      // Send også til AI for tolkning
      try {
        const aiRes = await fetch(`${API_BASE}/ai/upload-invoice-document`, {
          method: "POST",
          body: formData
        });
        if (aiRes.ok) {
          const aiData = await aiRes.json();
          // Klargjør bokføringsskjemaet med AI-forslag
          if (aiData.supplier) setPurchaseSupplier(aiData.supplier);
          if (aiData.total_amount) setPurchaseAmount(String(aiData.total_amount));
          if (aiData.suggested_expense_account) setPurchaseAccount(aiData.suggested_expense_account);
          setVoucherDesc(`Kjøp: ${aiData.supplier || file.name}`);
          setAttachedDocUrl(data.file_path);
          setActiveTab("record");
        }
      } catch (aiErr) {
        console.error("AI parse feilet:", aiErr);
      }
    } catch (err: any) {
      alert(`Feil ved opplasting: ${err.message}`);
    } finally {
      setUploadLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // 2. Bokfør bilag
  const handleBookVoucher = async () => {
    let linesToPost: VoucherLine[] = [];
    let desc = voucherDesc.trim() || "Kjøp";

    if (recordMode === "purchase") {
      const tot = parseFloat(purchaseAmount);
      if (isNaN(tot) || tot <= 0) {
        alert("Vennligst oppgi et gyldig beløp.");
        return;
      }

      const vatRate = parseFloat(purchaseVat) / 100.0;
      let vatAmt = 0;
      let netAmt = tot;

      if (vatRate > 0) {
        // Totalen inkluderer MVA
        netAmt = round(tot / (1 + vatRate), 2);
        vatAmt = round(tot - netAmt, 2);
      }

      linesToPost.push({
        account_number: purchaseAccount,
        description: `${desc} (netto)`,
        debit: netAmt,
        credit: 0
      });

      if (vatAmt > 0) {
        linesToPost.push({
          account_number: 2710, // Inngående MVA
          description: "Inngående MVA 25%",
          debit: vatAmt,
          credit: 0
        });
      }

      // Motpost: Bank (1920) eller Leverandørgjeld (2400)
      const creditAcc = purchasePaymentMethod === "bank" ? 1920 : 2400;
      linesToPost.push({
        account_number: creditAcc,
        description: purchasePaymentMethod === "bank" ? "Betalt fra driftskonto" : "Leverandørgjeld",
        debit: 0,
        credit: tot
      });
    } else if (recordMode === "free") {
      // Sjekk balanse
      const debSum = freeLines.reduce((s, l) => s + (l.debit || 0), 0);
      const credSum = freeLines.reduce((s, l) => s + (l.credit || 0), 0);
      if (Math.abs(debSum - credSum) > 0.01) {
        alert(`Bilaget er i ubalanse! Debet: ${debSum.toFixed(2)} NOK, Kredit: ${credSum.toFixed(2)} NOK.`);
        return;
      }
      linesToPost = freeLines;
    }

    try {
      const res = await fetch(`${API_BASE}/accounting/vouchers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: voucherDate ? new Date(voucherDate).toISOString() : new Date().toISOString(),
          description: desc,
          source_document: attachedDocUrl,
          lines: linesToPost
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Kunne ikke bokføre bilaget.");
      }

      alert("Bilag ble vellykket bokført i hovedboken!");
      setPurchaseAmount("");
      setVoucherDesc("");
      setAttachedDocUrl(null);
      fetchAllData();
      setActiveTab("vouchers");
    } catch (e: any) {
      alert(`Feil: ${e.message}`);
    }
  };

  // 3. Bankavstemning: Kjør auto-reconcile
  const handleAutoReconcile = async () => {
    try {
      const res = await fetch(`${API_BASE}/accounting/bank/auto-reconcile`, { method: "POST" });
      const data = await res.json();
      alert(data.message || "Automatisk avstemming fullført!");
      fetchAllData();
    } catch (e) {
      alert("Feil ved automatisk avstemming.");
    }
  };

  // 4. Bankavstemning: 1-klikks hurtigbokføring (Gebyr, rente, etc.)
  const handleQuickBookTx = async (txId: number, accountNum: number, desc: string) => {
    try {
      const res = await fetch(`${API_BASE}/accounting/bank/transactions/${txId}/quick-book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_number: accountNum, description: desc })
      });
      if (res.ok) {
        alert("Transaksjonen ble bokført og automatisk avstemt!");
        fetchAllData();
      } else {
        const err = await res.json();
        alert(`Feil: ${err.detail}`);
      }
    } catch (e) {
      alert("Feil ved hurtigbokføring.");
    }
  };

  // 5. Opprett Salgsfaktura (Conta Faktura)
  const handleCreateCustomerInvoice = async () => {
    if (!invCustomerName.trim()) {
      alert("Kundenavn må fylles ut.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/accounting/invoices`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: invCustomerName,
          customer_email: invCustomerEmail,
          due_date: new Date(invDueDate).toISOString(),
          lines: invLines
        })
      });
      if (!res.ok) throw new Error("Kunne ikke opprette faktura.");
      alert("Salgsfaktura opprettet og bokført automatisk!");
      setShowNewInvoiceModal(false);
      setInvCustomerName("");
      fetchAllData();
      setActiveTab("invoices");
    } catch (e: any) {
      alert(`Feil: ${e.message}`);
    }
  };

  // 6. Registrer innbetaling for faktura
  const handlePayInvoice = async (invoiceId: number) => {
    try {
      const res = await fetch(`${API_BASE}/accounting/invoices/${invoiceId}/pay`, { method: "POST" });
      if (res.ok) {
        alert("Innbetaling registrert på driftskonto 1920 og kundefordring lukket!");
        fetchAllData();
      }
    } catch (e) {
      alert("Feil ved registrering av betaling.");
    }
  };

  // 7. Betal leverandørfaktura
  const handlePaySupplierInvoice = async (invoiceId: number) => {
    try {
      const res = await fetch(`${API_BASE}/accounting/supplier-invoices/${invoiceId}/pay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_account: 1920 })
      });
      if (res.ok) {
        alert("Leverandørfaktura betalt fra bankkonto 1920!");
        fetchAllData();
      }
    } catch (e) {
      alert("Feil ved betaling.");
    }
  };

  // 8. Opprett leverandør
  const handleCreateSupplier = async () => {
    if (!newSupName.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/accounting/suppliers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newSupName,
          org_number: newSupOrgnr,
          account_number: newSupBankAcc,
          default_expense_account: newSupAccount,
          payment_terms_days: 14
        })
      });
      if (res.ok) {
        alert("Leverandør lagt til i leverandørregisteret!");
        setShowNewSupplierModal(false);
        setNewSupName("");
        fetchAllData();
      }
    } catch (e) {
      alert("Kunne ikke opprette leverandør.");
    }
  };

  // 9. Kundeservice svar
  const handleSendOperatorReply = async () => {
    if (!selectedTicket || !operatorReply.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/support/tickets/${selectedTicket.id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender: "OPERATOR_YOU",
          sender_name: "Deg (Kundeservice)",
          message: operatorReply
        })
      });
      if (res.ok) {
        setOperatorReply("");
        fetchAllData();
      }
    } catch (e) {
      alert("Kunne ikke sende melding.");
    }
  };

  // 10. CFO Chat
  const handleCfoAsk = async () => {
    if (!cfoQuestion.trim() || cfoLoading) return;
    const q = cfoQuestion;
    setCfoChatHistory(prev => [...prev, { sender: "user", text: q }]);
    setCfoQuestion("");
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
      setCfoChatHistory(prev => [
        ...prev,
        { sender: "cfo", text: "Beklager, kunne ikke nå CFO-motoren akkurat nå." }
      ]);
    } finally {
      setCfoLoading(false);
    }
  };

  // 11. Altinn MVA Innsending
  const handleSubmitVatToAltinn = async (term: number) => {
    setAltinnSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/accounting/altinn/submit-vat-return?term=${term}`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        setAltinnReceipt(data);
      } else {
        alert("Kunne ikke levere MVA-melding til Altinn.");
      }
    } catch (e) {
      alert("Feil ved innsending til Altinn.");
    } finally {
      setAltinnSubmitting(false);
    }
  };

  // 12. Brønnøysund Søk
  const handleBrregSearch = async (q: string) => {
    setBrregQuery(q);
    if (!q || q.trim().length < 2) {
      setBrregResults([]);
      return;
    }
    setBrregSearching(true);
    try {
      const res = await fetch(`${API_BASE}/accounting/brreg/search?q=${encodeURIComponent(q.trim())}`);
      if (res.ok) {
        const data = await res.json();
        setBrregResults(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setBrregSearching(false);
    }
  };

  // 13. SAF-T Financial XML v1.30 Eksport
  const handleDownloadSaft = async () => {
    try {
      const res = await fetch(`${API_BASE}/accounting/saft/export`);
      if (!res.ok) throw new Error("Feil fra server");
      const xmlBlob = await res.blob();
      const url = URL.createObjectURL(xmlBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SAF-T_Financial_Norway_${new Date().toISOString().split("T")[0]}.xml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Kunne ikke generere SAF-T XML eksport.");
    }
  };

  function round(val: number, decimals: number) {
    return Number(Math.round(Number(val + "e" + decimals)) + "e-" + decimals);
  }

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans antialiased overflow-hidden">
      {/* 1-sekunds logo-glimt (3/4 av skjermen) før innlogging / hovedside */}
      <LogoSplash durationMs={1000} />

      {/* Hidden file input for fast attachment upload */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        accept="image/*,application/pdf"
        className="hidden"
      />

      {/* --- SIDEBAR NAVIGATION (CONTA STYLE) --- */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col justify-between border-r border-slate-800 shadow-xl select-none z-20">
        <div>
          {/* Logo & Bedriftsnavn */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-black border border-amber-500/40 overflow-hidden flex items-center justify-center shadow-md shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/brand/logo.png" alt="Logo" className="w-full h-full object-contain" />
              </div>
              <div>
                <h1 className="font-bold text-white text-base tracking-tight leading-tight">Phink Accounting</h1>
                <p className="text-xs text-slate-400 truncate max-w-[130px]" title={companySettings.company_name}>
                  {companySettings.company_name}
                </p>
              </div>
            </div>
          </div>

          {/* Quick Action Button: + Før Regnskap */}
          <div className="p-3">
            <button
              onClick={() => {
                setActiveTab("record");
              }}
              className="w-full py-2.5 px-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-medium text-sm rounded-lg shadow-sm flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>+ Før regnskap</span>
            </button>
          </div>

          {/* Navigasjonselementer */}
          <nav className="px-2 space-y-0.5 text-sm overflow-y-auto max-h-[calc(100vh-250px)]">
            <button
              onClick={() => setActiveTab("overview")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "overview"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              <span>Oversikt</span>
            </button>

            <button
              onClick={() => setActiveTab("notifications")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "notifications"
                  ? "bg-amber-500/15 text-amber-300 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Bell className="w-4 h-4 text-amber-400" />
                <span>Varslinger</span>
              </div>
              {notificationCount > 0 && (
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-red-500 text-white">
                  {notificationCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("inbox")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "inbox"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center space-x-3">
                <FolderCheck className="w-4 h-4" />
                <span>Bilagsmottak</span>
              </div>
              {documents.length > 0 && (
                <span className="bg-blue-500/20 text-blue-300 text-xs px-2 py-0.5 rounded-full font-semibold">
                  {documents.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("vouchers")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "vouchers"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Bilagsliste & Journal</span>
            </button>

            <button
              onClick={() => setActiveTab("bank")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "bank"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Landmark className="w-4 h-4" />
                <span>Bank & Avstemning</span>
              </div>
              {summary.pending_reconciliations && summary.pending_reconciliations > 0 ? (
                <span className="bg-amber-500/20 text-amber-300 text-xs px-2 py-0.5 rounded-full font-semibold">
                  {summary.pending_reconciliations}
                </span>
              ) : null}
            </button>

            <div className="pt-3 pb-1 px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
              Salg & Kjøp
            </div>

            <button
              onClick={() => setActiveTab("invoices")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "invoices"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Receipt className="w-4 h-4" />
              <span>Faktura & Kunder</span>
            </button>

            <button
              onClick={() => setActiveTab("suppliers")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "suppliers"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Building2 className="w-4 h-4" />
              <span>Leverandører & Kjøp</span>
            </button>

            <button
              onClick={() => setActiveTab("payroll")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "payroll"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Users className="w-4 h-4 text-sky-400" />
              <span>Lønnskjøring (Auto)</span>
            </button>

            <button
              onClick={() => setActiveTab("archive")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "archive"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <FolderCheck className="w-4 h-4 text-amber-400" />
              <span>Bilagsarkiv</span>
            </button>

            <button
              onClick={() => setActiveTab("billing")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "billing"
                  ? "bg-orange-500/15 text-orange-300 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <CreditCard className="w-4 h-4 text-orange-400" />
              <span>Vipps &amp; Faktura</span>
            </button>

            <div className="pt-3 pb-1 px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
              Myndigheter & Rapporter
            </div>

            <button
              onClick={() => setActiveTab("vat")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "vat"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>MVA-melding</span>
            </button>

            <button
              onClick={() => setActiveTab("saft")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "saft"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Download className="w-4 h-4 text-emerald-400" />
              <span>SAF-T XML (Eksport/Import)</span>
            </button>

            <button
              onClick={() => setActiveTab("compliance")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "compliance"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileCheck className="w-4 h-4 text-violet-400" />
              <span>Regnskapsfaglig kontroll</span>
            </button>

            <button
              onClick={() => setActiveTab("altinn")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "altinn"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Landmark className="w-4 h-4 text-emerald-400" />
              <span>Altinn & Brreg</span>
            </button>

            <button
              onClick={() => setActiveTab("reports")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "reports"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Resultat & Balanse</span>
            </button>

            <button
              onClick={() => setActiveTab("accounts")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "accounts"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <CreditCard className="w-4 h-4" />
              <span>Kontoplan (NS 4102)</span>
            </button>

            <div className="pt-3 pb-1 px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
              Assistanse & Support
            </div>

            <button
              onClick={() => setActiveTab("cfo")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "cfo"
                  ? "bg-blue-600/15 text-blue-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>AI CFO Rådgiver</span>
            </button>

            <button
              onClick={() => setActiveTab("support")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "support"
                  ? "bg-emerald-600/15 text-emerald-400 font-semibold"
                  : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Headphones className="w-4 h-4 text-emerald-400" />
                <span>Kundeservice Desk</span>
              </div>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </button>
          </nav>
        </div>

        {/* Bunnprofil & Innstillinger */}
        <div className="p-3 border-t border-slate-800 space-y-1">
          {currentUser ? (
            <div className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs">
              <div className="font-semibold text-white truncate">{currentUser.company_name || currentUser.full_name}</div>
              <div className="text-[11px] text-slate-400 truncate">
                {currentUser.entity_type_label} {currentUser.org_number ? `· ${currentUser.org_number}` : ""}
              </div>
              <button
                onClick={() => {
                  localStorage.removeItem("phink_token");
                  setCurrentUser(null);
                }}
                className="mt-1.5 text-[11px] text-red-400 hover:text-red-300 cursor-pointer"
              >
                Logg ut ({currentUser.email})
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 transition-colors text-xs font-semibold cursor-pointer"
            >
              <User className="w-4 h-4" />
              <span>Logg inn / Ny konto</span>
            </button>
          )}
          <button
            onClick={() => setActiveTab("settings")}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors text-sm cursor-pointer"
          >
            <Settings className="w-4 h-4" />
            <span>Innstillinger</span>
          </button>
          <div className="mt-2 pt-2 border-t border-slate-800/50 flex items-center justify-between px-2 text-xs text-slate-400">
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              <span>Lokal Llama 3.1</span>
            </span>
            <span>v0.2 Enterprise</span>
          </div>
        </div>
      </aside>

      {/* --- MAIN WORKSPACE --- */}
      <main className="flex-1 flex flex-col overflow-hidden bg-slate-50">
        {/* Top Header */}
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-xs z-10">
          <div className="flex items-center space-x-4">
            <h2 className="text-base font-semibold text-slate-800 capitalize">
              {activeTab === "overview" && "Oversikt over bedriftens økonomi"}
              {activeTab === "notifications" && "Varslinger & Oppmerksomhetspunkter"}
              {activeTab === "inbox" && "Bilagsmottak (Innboks for kvitteringer & fakturaer)"}
              {activeTab === "record" && "Før nytt bilag (Veiviser)"}
              {activeTab === "vouchers" && "Bilagsjournal & Hovedbok"}
              {activeTab === "archive" && "Bilagsarkiv (Bokføringsloven § 13)"}
              {activeTab === "bank" && "Bank & Bankavstemning"}
              {activeTab === "invoices" && "Faktura & Kunder (Norsk MVA)"}
              {activeTab === "suppliers" && "Leverandører & Leverandørreskontro"}
              {activeTab === "payroll" && "Lønnskjøring med automatisk fordeling"}
              {activeTab === "billing" && "Betaling (Kun Vipps Bedrift & Tilsendt Faktura)"}
              {activeTab === "vat" && "MVA-melding & Oppgjør"}
              {activeTab === "altinn" && "Offentlig innsending (Altinn 3, Digdir Maskinporten & Brønnøysund)"}
              {activeTab === "saft" && "SAF-T Financial XML v1.30 (Eksport & Import)"}
              {activeTab === "compliance" && "Regnskapsfaglig kontroll & Saldobalanse"}
              {activeTab === "reports" && "Finansielle Rapporter"}
              {activeTab === "accounts" && "Norsk Standard Kontoplan (NS 4102)"}
              {activeTab === "cfo" && "Phink AI CFO (Meta Llama 3.1)"}
              {activeTab === "support" && "Live Kundeservicedesk (Human-in-the-Loop)"}
              {activeTab === "settings" && "Selskapsinnstillinger"}
            </h2>
          </div>

          <div className="flex items-center space-x-3">
            {/* Quick Upload Bilag Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadLoading}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg flex items-center space-x-1.5 border border-slate-200 transition-colors cursor-pointer"
            >
              <Upload className="w-4 h-4 text-slate-500" />
              <span>{uploadLoading ? "Laster opp..." : "Last opp bilag (PDF/Bilde)"}</span>
            </button>

            {/* Ny Salgsfaktura Snarvei */}
            <button
              onClick={() => setShowNewInvoiceModal(true)}
              className="px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 text-sm font-medium rounded-lg flex items-center space-x-1.5 border border-blue-200 transition-colors cursor-pointer"
            >
              <Receipt className="w-4 h-4 text-blue-600" />
              <span>Ny Faktura</span>
            </button>

            <button
              onClick={fetchAllData}
              title="Oppdater data"
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* TAB 1: OVERSIKT (DASHBOARD) */}
          {activeTab === "overview" && (
            <div className="max-w-6xl mx-auto space-y-6">
              {/* Top KPI Cards (Conta Look) */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Bankinnskudd (Driftskonto)</span>
                    <Landmark className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div className="mt-2 text-2xl font-bold text-slate-900">
                    {summary.bank_balance.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                  </div>
                  <div className="mt-1 text-xs text-emerald-600 flex items-center space-x-1">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Likviditetsreserve</span>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Utestående fra kunder</span>
                    <Receipt className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="mt-2 text-2xl font-bold text-slate-900">
                    {(summary.total_receivables || 0).toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                  </div>
                  <div className="mt-1 text-xs text-slate-500">Kundefordringer (Konto 1500)</div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Skyldig til leverandører</span>
                    <Building2 className="w-4 h-4 text-amber-600" />
                  </div>
                  <div className="mt-2 text-2xl font-bold text-slate-900">
                    {(summary.total_payables || 0).toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                  </div>
                  <div className="mt-1 text-xs text-slate-500">Leverandørgjeld (Konto 2400)</div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Driftsresultat i år</span>
                    <TrendingUp className="w-4 h-4 text-indigo-600" />
                  </div>
                  <div
                    className={`mt-2 text-2xl font-bold ${
                      summary.net_income >= 0 ? "text-emerald-600" : "text-rose-600"
                    }`}
                  >
                    {summary.net_income.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    Inntekter: {summary.total_revenue.toLocaleString("nb-NO")} NOK
                  </div>
                </div>
              </div>

              {/* Raske Handlinger & Bankavstemning Banner */}
              {summary.pending_reconciliations && summary.pending_reconciliations > 0 ? (
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 p-4 rounded-xl flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-amber-100 rounded-lg text-amber-700">
                      <Landmark className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-amber-900 text-sm">
                        Du har {summary.pending_reconciliations} uavstemte banktransaksjoner
                      </h4>
                      <p className="text-xs text-amber-700">
                        Stem av banken med ett klikk for å sikre at regnskapet og nettbanken stemmer 100%.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setActiveTab("bank")}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors cursor-pointer"
                  >
                    Gå til bankavstemning
                  </button>
                </div>
              ) : null}

              {/* Hovedinnhold Dashboard: Siste Bilag & Utestående Regninger */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Siste bokførte bilag */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-slate-800 text-sm flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-blue-600" />
                      <span>Siste bokførte bilag</span>
                    </h3>
                    <button
                      onClick={() => setActiveTab("vouchers")}
                      className="text-xs text-blue-600 hover:underline font-medium"
                    >
                      Se alle ({vouchers.length}) &rarr;
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {vouchers.slice(0, 5).map(v => (
                      <div
                        key={v.id}
                        onClick={() => setSelectedVoucherForDetail(v)}
                        className="p-3 bg-slate-50 hover:bg-slate-100/80 rounded-lg flex items-center justify-between text-xs transition-colors cursor-pointer border border-slate-100"
                      >
                        <div>
                          <div className="font-semibold text-slate-800">
                            #{v.voucher_number} &bull; {v.description}
                          </div>
                          <div className="text-slate-400 mt-0.5">
                            {new Date(v.date).toLocaleDateString("nb-NO")} &bull; {v.lines.length} posteringer
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="font-medium text-slate-700">
                            {v.lines[0]?.debit > 0
                              ? `${v.lines[0]?.debit.toLocaleString("nb-NO")} NOK`
                              : `${v.lines[0]?.credit.toLocaleString("nb-NO")} NOK`}
                          </span>
                          {v.source_document && (
                            <div className="text-[10px] text-blue-600 flex items-center justify-end space-x-0.5 mt-0.5">
                              <Eye className="w-3 h-3" />
                              <span>Har vedlegg</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {vouchers.length === 0 && (
                      <p className="text-xs text-slate-400 py-4 text-center">Ingen bilag bokført ennå.</p>
                    )}
                  </div>
                </div>

                {/* Utestående salgsfakturaer */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-slate-800 text-sm flex items-center space-x-2">
                      <Receipt className="w-4 h-4 text-emerald-600" />
                      <span>Utestående Salgsfakturaer</span>
                    </h3>
                    <button
                      onClick={() => setActiveTab("invoices")}
                      className="text-xs text-blue-600 hover:underline font-medium"
                    >
                      Se fakturaoversikt &rarr;
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {invoices.filter(i => i.status !== "PAID").slice(0, 5).map(inv => (
                      <div
                        key={inv.id}
                        className="p-3 bg-slate-50 rounded-lg flex items-center justify-between text-xs border border-slate-100"
                      >
                        <div>
                          <div className="font-semibold text-slate-800">
                            Faktura #{inv.invoice_number} &bull; {inv.customer_name}
                          </div>
                          <div className="text-slate-400 mt-0.5">
                            Forfall: {new Date(inv.due_date).toLocaleDateString("nb-NO")} &bull; KID: {inv.kid}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-slate-900">
                            {inv.total_amount.toLocaleString("nb-NO")} NOK
                          </span>
                          <button
                            onClick={() => handlePayInvoice(inv.id)}
                            className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium cursor-pointer"
                          >
                            Registrer innbetaling
                          </button>
                        </div>
                      </div>
                    ))}
                    {invoices.filter(i => i.status !== "PAID").length === 0 && (
                      <p className="text-xs text-slate-400 py-4 text-center">
                        Ingen utestående kundefakturaer! Alt er betalt.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: BILAGSMOTTAK (INBOKS FOR BILAG & UPLOAD) */}
          {activeTab === "inbox" && (
            <div className="max-w-5xl mx-auto space-y-6">
              {/* Drag and Drop Upload Area */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-blue-300 hover:border-blue-500 bg-blue-50/40 hover:bg-blue-50/70 p-8 rounded-2xl text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-3"
              >
                <div className="w-14 h-14 rounded-2xl bg-blue-600/10 text-blue-600 flex items-center justify-center">
                  <FileUp className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-base">
                    Dra og slipp bilaget ditt her, eller klikk for å velge fil
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Støtter både <strong>PDF-fakturaer</strong> og <strong>bilder</strong> (PNG, JPG, JPEG, WEBP).
                  </p>
                </div>
                <button
                  type="button"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
                >
                  Velg bilag fra datamaskinen
                </button>
              </div>

              {uploadSuccessMsg && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span>{uploadSuccessMsg}</span>
                </div>
              )}

              {/* Dokumentliste i innboksen */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-800 text-sm">
                    Mottatte bilag i innboksen ({documents.length})
                  </h3>
                  <span className="text-xs text-slate-500">
                    Klikk &quot;Før bilag&quot; for å kontere med AI-assistanse
                  </span>
                </div>

                <div className="divide-y divide-slate-100">
                  {documents.map(doc => (
                    <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 font-bold text-xs uppercase">
                          {doc.file_type}
                        </div>
                        <div>
                          <div className="font-semibold text-sm text-slate-800">{doc.original_name}</div>
                          <div className="text-xs text-slate-400 mt-0.5">
                            Lastet opp {new Date(doc.uploaded_at).toLocaleString("nb-NO")} &bull;{" "}
                            {(doc.file_size / 1024).toFixed(1)} KB
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        {/* Vis forhåndsvisning */}
                        <button
                          onClick={() => {
                            setPreviewFileUrl(`http://localhost:8000${doc.file_path}`);
                            setPreviewFileType(doc.file_type === "pdf" ? "pdf" : "image");
                          }}
                          className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium flex items-center space-x-1 cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Se bilag</span>
                        </button>

                        {/* Før bilag */}
                        <button
                          onClick={() => {
                            setAttachedDocUrl(doc.file_path);
                            setVoucherDesc(`Kjøp: ${doc.original_name}`);
                            setActiveTab("record");
                          }}
                          className="px-3.5 py-1.5 text-xs text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold flex items-center space-x-1 cursor-pointer"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Før dette bilaget</span>
                        </button>
                      </div>
                    </div>
                  ))}
                  {documents.length === 0 && (
                    <div className="p-10 text-center text-slate-400 text-xs">
                      Ingen bilag i innboksen for øyeblikket. Last opp et bilde eller en PDF ovenfor for å starte!
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: FØR REGNSKAP (CONTA VEIVISER) */}
          {activeTab === "record" && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">Bokføringsveiviser</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Før utgifter, salg eller manuelle posteringer med matematisk validering av dobbel bokføring.
                  </p>
                </div>

                {/* Valg av type føring (Conta stil) */}
                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => setRecordMode("purchase")}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      recordMode === "purchase"
                        ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/20"
                        : "border-slate-200 hover:border-slate-300 text-slate-700"
                    }`}
                  >
                    <div className="font-semibold text-sm">Kjøp / Utgift</div>
                    <div className="text-xs text-slate-500 mt-0.5">Kvittering eller leverandørfaktura</div>
                  </button>

                  <button
                    onClick={() => {
                      setRecordMode("sale");
                      setShowNewInvoiceModal(true);
                    }}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      recordMode === "sale"
                        ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/20"
                        : "border-slate-200 hover:border-slate-300 text-slate-700"
                    }`}
                  >
                    <div className="font-semibold text-sm">Salg / Inntekt</div>
                    <div className="text-xs text-slate-500 mt-0.5">Send faktura til kunde</div>
                  </button>

                  <button
                    onClick={() => setRecordMode("free")}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      recordMode === "free"
                        ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-2 ring-blue-500/20"
                        : "border-slate-200 hover:border-slate-300 text-slate-700"
                    }`}
                  >
                    <div className="font-semibold text-sm">Fritt bilag</div>
                    <div className="text-xs text-slate-500 mt-0.5">Manuell debet og kredit</div>
                  </button>
                </div>

                {attachedDocUrl && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between text-xs text-blue-900">
                    <div className="flex items-center space-x-2">
                      <FolderCheck className="w-4 h-4 text-blue-600" />
                      <span>
                        Koblet vedlegg: <strong>{attachedDocUrl.split("/").pop()}</strong>
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        setPreviewFileUrl(`http://localhost:8000${attachedDocUrl}`);
                        setPreviewFileType(attachedDocUrl.endsWith(".pdf") ? "pdf" : "image");
                      }}
                      className="text-blue-600 hover:underline font-semibold flex items-center space-x-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Forhåndsvis vedlegg</span>
                    </button>
                  </div>
                )}

                {/* Skjema for Kjøp / Utgift */}
                {recordMode === "purchase" && (
                  <div className="space-y-4 pt-2">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Dato</label>
                        <input
                          type="date"
                          value={voucherDate}
                          onChange={e => setVoucherDate(e.target.value)}
                          className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Leverandør / Butikk</label>
                        <input
                          type="text"
                          placeholder="F.eks. Elkjøp, Google, Telenor..."
                          value={purchaseSupplier}
                          onChange={e => {
                            setPurchaseSupplier(e.target.value);
                            if (!voucherDesc) setVoucherDesc(`Kjøp fra ${e.target.value}`);
                          }}
                          className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-blue-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Beskrivelse</label>
                      <input
                        type="text"
                        placeholder="Hva gjelder kjøpet?"
                        value={voucherDesc}
                        onChange={e => setVoucherDesc(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-blue-500"
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Totalbeløp inkl. MVA (NOK)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="1250.00"
                          value={purchaseAmount}
                          onChange={e => setPurchaseAmount(e.target.value)}
                          className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg font-semibold text-slate-900 focus:outline-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">MVA-sats</label>
                        <select
                          value={purchaseVat}
                          onChange={e => setPurchaseVat(e.target.value)}
                          className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-blue-500"
                        >
                          <option value="25">25% (Standard høy sats)</option>
                          <option value="15">15% (Næringsmidler og mat)</option>
                          <option value="0">0% (Avgiftsfritt / Ingen MVA)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Kostnadskonto</label>
                        <select
                          value={purchaseAccount}
                          onChange={e => setPurchaseAccount(Number(e.target.value))}
                          className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-blue-500"
                        >
                          {accounts
                            .filter(a => a.account_number >= 4000 && a.account_number < 8000)
                            .map(a => (
                              <option key={a.account_number} value={a.account_number}>
                                {a.account_number} - {a.name}
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Betalingsmåte</label>
                      <div className="flex items-center space-x-4 text-xs font-medium text-slate-700">
                        <label className="flex items-center space-x-1.5 cursor-pointer">
                          <input
                            type="radio"
                            name="paym"
                            checked={purchasePaymentMethod === "bank"}
                            onChange={() => setPurchasePaymentMethod("bank")}
                          />
                          <span>Betalt fra Bankkonto (Konto 1920)</span>
                        </label>
                        <label className="flex items-center space-x-1.5 cursor-pointer">
                          <input
                            type="radio"
                            name="paym"
                            checked={purchasePaymentMethod === "supplier_credit"}
                            onChange={() => setPurchasePaymentMethod("supplier_credit")}
                          />
                          <span>Ubetalt faktura (Konto 2400 Leverandørgjeld)</span>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Skjema for Fritt bilag */}
                {recordMode === "free" && (
                  <div className="space-y-4 pt-2">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Dato</label>
                        <input
                          type="date"
                          value={voucherDate}
                          onChange={e => setVoucherDate(e.target.value)}
                          className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Bilagsbeskrivelse</label>
                        <input
                          type="text"
                          value={voucherDesc}
                          onChange={e => setVoucherDesc(e.target.value)}
                          placeholder="F.eks. Månedlig avskrivning eller lån..."
                          className="w-full px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg"
                        />
                      </div>
                    </div>

                    <div className="border border-slate-200 rounded-xl overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                          <tr>
                            <th className="py-2.5 px-3 text-left">Konto</th>
                            <th className="py-2.5 px-3 text-left">Tekst</th>
                            <th className="py-2.5 px-3 text-right">Debet (NOK)</th>
                            <th className="py-2.5 px-3 text-right">Kredit (NOK)</th>
                            <th className="w-8"></th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {freeLines.map((line, idx) => (
                            <tr key={idx}>
                              <td className="p-2">
                                <select
                                  value={line.account_number}
                                  onChange={e => {
                                    const val = Number(e.target.value);
                                    const next = [...freeLines];
                                    next[idx].account_number = val;
                                    setFreeLines(next);
                                  }}
                                  className="w-full px-2 py-1 text-xs border border-slate-200 rounded"
                                >
                                  {accounts.map(a => (
                                    <option key={a.account_number} value={a.account_number}>
                                      {a.account_number} - {a.name}
                                    </option>
                                  ))}
                                </select>
                              </td>
                              <td className="p-2">
                                <input
                                  type="text"
                                  value={line.description}
                                  onChange={e => {
                                    const next = [...freeLines];
                                    next[idx].description = e.target.value;
                                    setFreeLines(next);
                                  }}
                                  className="w-full px-2 py-1 text-xs border border-slate-200 rounded"
                                />
                              </td>
                              <td className="p-2 text-right">
                                <input
                                  type="number"
                                  step="0.01"
                                  value={line.debit || ""}
                                  onChange={e => {
                                    const next = [...freeLines];
                                    next[idx].debit = parseFloat(e.target.value) || 0;
                                    setFreeLines(next);
                                  }}
                                  className="w-24 px-2 py-1 text-xs border border-slate-200 rounded text-right font-medium"
                                />
                              </td>
                              <td className="p-2 text-right">
                                <input
                                  type="number"
                                  step="0.01"
                                  value={line.credit || ""}
                                  onChange={e => {
                                    const next = [...freeLines];
                                    next[idx].credit = parseFloat(e.target.value) || 0;
                                    setFreeLines(next);
                                  }}
                                  className="w-24 px-2 py-1 text-xs border border-slate-200 rounded text-right font-medium"
                                />
                              </td>
                              <td className="p-2 text-center">
                                {freeLines.length > 2 && (
                                  <button
                                    onClick={() => setFreeLines(freeLines.filter((_, i) => i !== idx))}
                                    className="text-slate-400 hover:text-rose-500"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot className="bg-slate-50 font-semibold text-slate-800">
                          <tr>
                            <td colSpan={2} className="py-2 px-3">
                              <button
                                onClick={() =>
                                  setFreeLines([
                                    ...freeLines,
                                    { account_number: 6800, description: "", debit: 0, credit: 0 }
                                  ])
                                }
                                className="text-blue-600 hover:underline text-xs"
                              >
                                + Legg til linje
                              </button>
                            </td>
                            <td className="py-2 px-3 text-right">
                              {freeLines.reduce((s, l) => s + (l.debit || 0), 0).toFixed(2)} NOK
                            </td>
                            <td className="py-2 px-3 text-right">
                              {freeLines.reduce((s, l) => s + (l.credit || 0), 0).toFixed(2)} NOK
                            </td>
                            <td></td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                  <div className="text-xs text-slate-500 flex items-center space-x-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Dobbel bokføring valideres matematisk før lagring</span>
                  </div>
                  <button
                    onClick={handleBookVoucher}
                    className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-xl shadow-sm transition-all cursor-pointer"
                  >
                    Bokfør bilag nå
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: BILAGSLISTE & JOURNAL */}
          {activeTab === "vouchers" && (
            <div className="max-w-6xl mx-auto space-y-4">
              <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-800 text-sm">
                    Bilagsjournal / Hovedbok ({vouchers.length} bilag)
                  </h3>
                  <button
                    onClick={() => setActiveTab("record")}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold"
                  >
                    + Nytt bilag
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4">Bilag #</th>
                        <th className="py-3 px-4">Dato</th>
                        <th className="py-3 px-4">Beskrivelse</th>
                        <th className="py-3 px-4">Linjer (Debet / Kredit)</th>
                        <th className="py-3 px-4 text-right">Beløp</th>
                        <th className="py-3 px-4 text-center">Vedlegg</th>
                        <th className="py-3 px-4 text-center">Handling</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {vouchers.map(v => {
                        const totalDebit = v.lines.reduce((s, l) => s + l.debit, 0);
                        return (
                          <tr key={v.id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-3 px-4 font-bold text-slate-800">#{v.voucher_number}</td>
                            <td className="py-3 px-4 text-slate-600">
                              {new Date(v.date).toLocaleDateString("nb-NO")}
                            </td>
                            <td className="py-3 px-4 font-medium text-slate-900">{v.description}</td>
                            <td className="py-3 px-4 text-slate-500">
                              <span className="font-mono text-[11px]">
                                {v.lines.map(l => l.account_number).join(" / ")}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right font-bold text-slate-900">
                              {totalDebit.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                            </td>
                            <td className="py-3 px-4 text-center">
                              {v.source_document ? (
                                <button
                                  onClick={() => {
                                    setPreviewFileUrl(`http://localhost:8000${v.source_document}`);
                                    setPreviewFileType(v.source_document?.endsWith(".pdf") ? "pdf" : "image");
                                  }}
                                  className="text-blue-600 hover:text-blue-800 font-medium flex items-center justify-center space-x-1 cursor-pointer mx-auto"
                                >
                                  <Eye className="w-3.5 h-3.5" />
                                  <span>Se fil</span>
                                </button>
                              ) : (
                                <span className="text-slate-300">-</span>
                              )}
                            </td>
                            <td className="py-3 px-4 text-center">
                              <button
                                onClick={() => setSelectedVoucherForDetail(v)}
                                className="px-2.5 py-1 text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded text-[11px] font-medium cursor-pointer"
                              >
                                Vis linjer
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: BANK & BANKAVSTEMNING (DEN STORE FUNKSJONEN!) */}
          {activeTab === "bank" && (
            <div className="max-w-6xl mx-auto space-y-6">
              {/* Avstemmingsstatus Kort */}
              {bankSummary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                    <div className="text-xs text-slate-500 font-medium">Saldo ifølge bankutskrift</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">
                      {bankSummary.bank_statement_balance.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                    </div>
                    <div className="text-xs text-slate-400 mt-1">Sum av importerte transaksjoner</div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                    <div className="text-xs text-slate-500 font-medium">Bokført saldo i regnskapet (Konto 1920)</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">
                      {bankSummary.account_1920_balance.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                    </div>
                    <div className="text-xs text-slate-400 mt-1">Hovedbok saldo driftskonto</div>
                  </div>

                  <div
                    className={`p-5 rounded-xl border shadow-xs ${
                      bankSummary.is_balanced
                        ? "bg-emerald-50/60 border-emerald-200 text-emerald-900"
                        : "bg-amber-50/60 border-amber-200 text-amber-900"
                    }`}
                  >
                    <div className="text-xs font-medium">Avstemmingsdifferanse</div>
                    <div className="text-2xl font-bold mt-1">
                      {bankSummary.difference.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                    </div>
                    <div className="text-xs mt-1 flex items-center space-x-1 font-semibold">
                      {bankSummary.is_balanced ? (
                        <>
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Banken er 100% avstemt!</span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                          <span>Må avstemmes mot manglende poster</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Handlingsknapper Bank */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Banktransaksjoner (Kontoutskrift)</h3>
                  <p className="text-xs text-slate-500">
                    Sammenlign transaksjoner fra nettbanken med regnskapet. Bruk hurtigbokføring for gebyrer og renter.
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleAutoReconcile}
                    className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs rounded-lg shadow-xs flex items-center space-x-1.5 transition-all cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Kjør automatisk avstemming</span>
                  </button>
                </div>
              </div>

              {/* Transaksjonsliste */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                    <tr>
                      <th className="py-3 px-4">Dato</th>
                      <th className="py-3 px-4">Beskrivelse / Tekst</th>
                      <th className="py-3 px-4">Referanse / KID</th>
                      <th className="py-3 px-4 text-right">Beløp (Inn / Ut)</th>
                      <th className="py-3 px-4 text-center">Status</th>
                      <th className="py-3 px-4 text-right">Hurtighandling</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {bankTransactions.map(tx => (
                      <tr key={tx.id} className="hover:bg-slate-50">
                        <td className="py-3 px-4 text-slate-600">
                          {new Date(tx.transaction_date).toLocaleDateString("nb-NO")}
                        </td>
                        <td className="py-3 px-4 font-semibold text-slate-900">{tx.description}</td>
                        <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">{tx.reference || "-"}</td>
                        <td
                          className={`py-3 px-4 text-right font-bold ${
                            tx.amount >= 0 ? "text-emerald-600" : "text-slate-900"
                          }`}
                        >
                          {tx.amount >= 0 ? "+" : ""}
                          {tx.amount.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                        </td>
                        <td className="py-3 px-4 text-center">
                          {tx.reconciled ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                              <Check className="w-3 h-3 mr-1" /> Avstemt
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800">
                              Uavstemt
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {!tx.reconciled ? (
                            <div className="flex items-center justify-end space-x-1.5">
                              {/* Hvis gebyr */}
                              {tx.amount < 0 && (
                                <button
                                  onClick={() =>
                                    handleQuickBookTx(tx.id, 7770, `Bankgebyr: ${tx.description}`)
                                  }
                                  className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium cursor-pointer"
                                >
                                  Bokfør som gebyr (7770)
                                </button>
                              )}
                              {/* Hvis renteinntekt */}
                              {tx.amount > 0 && (
                                <button
                                  onClick={() =>
                                    handleQuickBookTx(tx.id, 8050, `Renteinntekt: ${tx.description}`)
                                  }
                                  className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium cursor-pointer"
                                >
                                  Bokfør som rente (8050)
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  setPurchaseAmount(String(Math.abs(tx.amount)));
                                  setVoucherDesc(tx.description);
                                  setActiveTab("record");
                                }}
                                className="px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded text-[11px] font-medium cursor-pointer"
                              >
                                Før bilag
                              </button>
                            </div>
                          ) : (
                            <span className="text-slate-400 text-[11px]">OK</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: FAKTURA & KUNDER (CONTA FAKTURA) */}
          {activeTab === "invoices" && (
            <div className="max-w-6xl mx-auto space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Conta Faktura & Kunder</h3>
                  <p className="text-xs text-slate-500">
                    Opprett profesjonelle salgsfakturaer med automatisk bokføring, KID og forfallsoppfølging.
                  </p>
                </div>
                <button
                  onClick={() => setShowNewInvoiceModal(true)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-xs flex items-center space-x-1.5 cursor-pointer"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>+ Opprett ny salgsfaktura</span>
                </button>
              </div>

              {/* Fakturatabell */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                    <tr>
                      <th className="py-3 px-4">Faktura #</th>
                      <th className="py-3 px-4">Kunde</th>
                      <th className="py-3 px-4">Dato</th>
                      <th className="py-3 px-4">Forfallsdato</th>
                      <th className="py-3 px-4">KID</th>
                      <th className="py-3 px-4 text-right">Beløp inkl. MVA</th>
                      <th className="py-3 px-4 text-center">Status</th>
                      <th className="py-3 px-4 text-right">Handling</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {invoices.map(inv => (
                      <tr key={inv.id} className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-bold text-slate-900">#{inv.invoice_number}</td>
                        <td className="py-3 px-4 font-semibold text-slate-800">{inv.customer_name}</td>
                        <td className="py-3 px-4 text-slate-600">
                          {new Date(inv.issue_date).toLocaleDateString("nb-NO")}
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          {new Date(inv.due_date).toLocaleDateString("nb-NO")}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-500">{inv.kid || "-"}</td>
                        <td className="py-3 px-4 text-right font-bold text-slate-900">
                          {inv.total_amount.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                        </td>
                        <td className="py-3 px-4 text-center">
                          {inv.status === "PAID" ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                              <Check className="w-3 h-3 mr-1" /> Betalt
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-800">
                              Utestående
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {inv.status !== "PAID" && (
                            <button
                              onClick={() => handlePayInvoice(inv.id)}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium cursor-pointer"
                            >
                              Registrer betaling
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {invoices.length === 0 && (
                      <tr>
                        <td colSpan={8} className="p-8 text-center text-slate-400">
                          Ingen salgsfakturaer opprettet ennå.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 7: LEVERANDØRER & LEVERANDØRRESKONTRO */}
          {activeTab === "suppliers" && (
            <div className="max-w-6xl mx-auto space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Leverandører & Leverandørreskontro</h3>
                  <p className="text-xs text-slate-500">
                    Oversikt over leverandører, utestående leverandørgjeld og inngående regninger.
                  </p>
                </div>
                <button
                  onClick={() => setShowNewSupplierModal(true)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-xs flex items-center space-x-1.5 cursor-pointer"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>+ Ny Leverandør</span>
                </button>
              </div>

              {/* Leverandørkort */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {suppliers.map(sup => (
                  <div key={sup.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-slate-900 text-sm">{sup.name}</h4>
                      <Building2 className="w-4 h-4 text-slate-400" />
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">Org.nr: {sup.org_number || "Ikke registrert"}</div>
                    <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                      <span className="text-slate-500">Utestående gjeld:</span>
                      <span
                        className={`font-bold ${
                          sup.outstanding_balance > 0 ? "text-amber-600" : "text-slate-900"
                        }`}
                      >
                        {sup.outstanding_balance.toLocaleString("nb-NO")} NOK
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Inngående leverandørfakturaer */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                <div className="p-4 border-b border-slate-200 font-semibold text-slate-800 text-sm">
                  Inngående Fakturaer & Regninger
                </div>
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                    <tr>
                      <th className="py-3 px-4">Leverandør</th>
                      <th className="py-3 px-4">Fakturanummer</th>
                      <th className="py-3 px-4">Forfallsdato</th>
                      <th className="py-3 px-4">KID</th>
                      <th className="py-3 px-4 text-right">Beløp</th>
                      <th className="py-3 px-4 text-center">Status</th>
                      <th className="py-3 px-4 text-right">Handling</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {supplierInvoices.map(inv => (
                      <tr key={inv.id} className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-bold text-slate-900">{inv.supplier_name}</td>
                        <td className="py-3 px-4 text-slate-600">{inv.invoice_number}</td>
                        <td className="py-3 px-4 text-slate-600">
                          {new Date(inv.due_date).toLocaleDateString("nb-NO")}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-500">{inv.kid || "-"}</td>
                        <td className="py-3 px-4 text-right font-bold text-slate-900">
                          {inv.total_amount.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                        </td>
                        <td className="py-3 px-4 text-center">
                          {inv.status === "PAID" ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                              Betalt
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800">
                              Ubetalt
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {inv.status !== "PAID" && (
                            <button
                              onClick={() => handlePaySupplierInvoice(inv.id)}
                              className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-semibold cursor-pointer"
                            >
                              Betal fra bank
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 8: MVA-MELDING */}
          {activeTab === "vat" && (
            <div className="max-w-5xl mx-auto space-y-6">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">MVA-Melding (Merverdiavgift)</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Beregnet for 2-månedlige terminer i henhold til Skatteetatens standarder.
                    </p>
                  </div>
                  <div className="px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-semibold">
                    MVA-Registrert: Ja (25% Alminnelig sats)
                  </div>
                </div>

                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                  {vatReports.map(term => (
                    <div key={term.term} className="p-4 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-bold text-slate-900 text-sm">{term.term_name}</div>
                        <div className="text-slate-400 mt-0.5">
                          Avgiftspliktig omsetning: {term.base_sales_high_25.toLocaleString("nb-NO")} NOK
                        </div>
                      </div>

                      <div className="flex items-center space-x-6 text-right">
                        <div>
                          <div className="text-slate-400">Utgående MVA (25%)</div>
                          <div className="font-semibold text-slate-800">
                            +{term.output_vat_25.toLocaleString("nb-NO")} NOK
                          </div>
                        </div>

                        <div>
                          <div className="text-slate-400">Inngående MVA (Fradrag)</div>
                          <div className="font-semibold text-slate-800">
                            -{term.input_vat_deductible.toLocaleString("nb-NO")} NOK
                          </div>
                        </div>

                        <div className="border-l border-slate-200 pl-6">
                          <div className="text-slate-500 font-semibold">Netto å betale</div>
                          <div
                            className={`font-bold text-sm ${
                              term.net_vat_payable >= 0 ? "text-slate-900" : "text-emerald-600"
                            }`}
                          >
                            {term.net_vat_payable.toLocaleString("nb-NO")} NOK
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Lever til Altinn knapp */}
                <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                  <div className="text-xs text-slate-500">
                    Klar til å levere MVA-oppgave for aktiv termin (Termin 6)?
                  </div>
                  <button
                    onClick={() => handleSubmitVatToAltinn(6)}
                    disabled={altinnSubmitting}
                    className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center space-x-2 cursor-pointer transition-all"
                  >
                    <ShieldCheck className="w-4 h-4" />
                    <span>{altinnSubmitting ? "Sender til Altinn..." : "Send MVA-melding til Altinn / Skatteetaten"}</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB: ALTINN, MASKINPORTEN & BRØNNØYSUNDREGISTRENE */}
          {activeTab === "altinn" && (
            <div className="max-w-5xl mx-auto space-y-6">
              {/* Header Banner Maskinporten */}
              <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6 rounded-2xl shadow-lg border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-lg border border-emerald-500/30">
                      🏛️
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-base">Digdir Maskinporten & Altinn 3 Integrasjon</h3>
                      <p className="text-xs text-slate-400">Offisiell systeminnsending for Skatteetaten og Brønnøysundregistrene</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 px-3 py-1 bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 rounded-full text-xs font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>Maskinporten Aktiv</span>
                  </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                  Dette er motoren de store regnskapssystemene (Conta, Fiken, Tripletex) kobler seg til. 
                  Gjennom Digitaliseringsdirektoratets (Digdir) <strong>Maskinporten</strong> autentiseres regnskapsprogrammet 
                  for direkte levering av <strong>MVA-melding</strong>, <strong>A-melding</strong>, og <strong>Årsregnskap</strong>.
                </p>
              </div>

              {/* Seksjon 1: Brønnøysundregistrene Live Oppslag */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                      <Search className="w-4 h-4 text-blue-600" />
                      <span>Brønnøysundregistrene (Enhetsregisteret Live Oppslag)</span>
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Søk i sanntid blant alle norske bedrifter via Brreg sitt åpne API (data.brreg.no).
                    </p>
                  </div>
                  <span className="text-[11px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono">
                    data.brreg.no
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <div className="relative flex-1">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      placeholder="Skriv firmanavn eller 9-sifret org.nr (f.eks. Conta, Equinor, DNB, Telenor)..."
                      value={brregQuery}
                      onChange={e => handleBrregSearch(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 text-xs bg-white border border-slate-200 rounded-xl focus:outline-blue-500 shadow-2xs"
                    />
                  </div>
                  {brregSearching && (
                    <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" />
                  )}
                </div>

                {/* Brreg Resultatliste */}
                {brregResults.length > 0 && (
                  <div className="border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100 max-h-72 overflow-y-auto">
                    {brregResults.map(b => (
                      <div key={b.org_number} className="p-3.5 hover:bg-slate-50 flex items-center justify-between text-xs transition-colors">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-900 text-sm">{b.name}</span>
                            <span className="font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">
                              {b.org_number}
                            </span>
                            <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-semibold">
                              {b.org_form}
                            </span>
                            {b.is_vat_registered ? (
                              <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-semibold flex items-center space-x-0.5">
                                <Check className="w-2.5 h-2.5" />
                                <span>MVA-registrert</span>
                              </span>
                            ) : (
                              <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-medium">
                                Ikke MVA
                              </span>
                            )}
                          </div>
                          <div className="text-slate-400 text-[11px] mt-1">
                            {b.address ? `${b.address}, ` : ""}{b.postal_code} {b.city}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setNewSupName(b.name);
                              setNewSupOrgnr(b.org_number);
                              setShowNewSupplierModal(true);
                            }}
                            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-semibold cursor-pointer"
                          >
                            + Legg til som leverandør
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Seksjon 2: SAF-T Regnskapseksport */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                <div className="space-y-1">
                  <h4 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                    <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
                    <span>SAF-T Regnskapseksport (Standard Audit File-Tax)</span>
                  </h4>
                  <p className="text-xs text-slate-500 max-w-xl">
                    Offisiell standard regnskapsfil (OECD XML / NS 4102) som Skatteetaten krever ved bokettersyn 
                    eller når ekstern revisor skal hente ut hovedbok og alle transaksjoner.
                  </p>
                </div>
                <button
                  onClick={handleDownloadSaft}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center space-x-2 cursor-pointer transition-colors"
                >
                  <Download className="w-4 h-4" />
                  <span>Last ned SAF-T fil</span>
                </button>
              </div>

              {/* Seksjon 3: Tjenesteoversikt Altinn 3 */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                <h4 className="font-bold text-slate-900 text-sm">
                  Aktiverte grensesnitt mot offentlige registre
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1 text-xs">
                    <div className="font-bold text-slate-900">Skatteetaten MVA</div>
                    <div className="text-slate-500 text-[11px]">Systeminnsending via Maskinporten</div>
                    <div className="pt-2 text-emerald-600 font-semibold flex items-center space-x-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Klar for Termin 1–6</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1 text-xs">
                    <div className="font-bold text-slate-900">A-melding (Lønn & AGA)</div>
                    <div className="text-slate-500 text-[11px]">Altinn 3 / Skatteetaten & NAV</div>
                    <div className="pt-2 text-emerald-600 font-semibold flex items-center space-x-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>EDAG 2.0 protokoll</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1 text-xs">
                    <div className="font-bold text-slate-900">Regnskapsregisteret (Brreg)</div>
                    <div className="text-slate-500 text-[11px]">Årsregnskap (RR-0002)</div>
                    <div className="pt-2 text-emerald-600 font-semibold flex items-center space-x-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Resultat & Balanse</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: FINANSIELLE RAPPORTER (RESULTAT & BALANSE) */}
          {activeTab === "reports" && (
            <div className="max-w-5xl mx-auto space-y-6">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">Resultatregnskap (P&L)</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Sammenstilling av driftsinntekter og driftskostnader for regnskapsåret.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="border-b border-slate-200 pb-2 flex items-center justify-between font-bold text-sm text-slate-900">
                    <span>Driftsinntekter (Salgsinntekt 25% mva)</span>
                    <span>{summary.total_revenue.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK</span>
                  </div>

                  <div className="border-b border-slate-200 pb-2 flex items-center justify-between font-bold text-sm text-slate-900">
                    <span>Driftskostnader (Varekjøp, IT, Leie, Administrasjon)</span>
                    <span className="text-rose-600">
                      -{summary.total_expenses.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                    </span>
                  </div>

                  <div className="pt-2 flex items-center justify-between font-extrabold text-base text-slate-900 bg-slate-50 p-4 rounded-xl">
                    <span>Driftsresultat / Årsresultat før skatt</span>
                    <span className={summary.net_income >= 0 ? "text-emerald-600" : "text-rose-600"}>
                      {summary.net_income.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 10: KONTOPLAN (NS 4102) */}
          {activeTab === "accounts" && (
            <div className="max-w-5xl mx-auto space-y-4">
              <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-800 text-sm">
                    Norsk Standard Kontoplan NS 4102 ({accounts.length} kontoer)
                  </h3>
                  <div className="text-xs text-slate-500">Klasse 1-8</div>
                </div>

                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                    <tr>
                      <th className="py-3 px-4">Kontonummer</th>
                      <th className="py-3 px-4">Kontonavn</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">MVA-kode</th>
                      <th className="py-3 px-4">Beskrivelse</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {accounts.map(acc => (
                      <tr key={acc.account_number} className="hover:bg-slate-50">
                        <td className="py-2.5 px-4 font-mono font-bold text-blue-600">{acc.account_number}</td>
                        <td className="py-2.5 px-4 font-semibold text-slate-800">{acc.name}</td>
                        <td className="py-2.5 px-4 text-slate-500">{acc.account_type}</td>
                        <td className="py-2.5 px-4 font-mono text-slate-500">{acc.vat_code || "-"}</td>
                        <td className="py-2.5 px-4 text-slate-400">{acc.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 11: AI CFO (LLAMA 3.1) */}
          {activeTab === "cfo" && (
            <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-purple-50 to-indigo-50 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center shadow-sm">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">Phink AI CFO (Meta Llama 3.1)</h3>
                    <p className="text-xs text-purple-700">Digital økonomisjef med sanntidstilgang til regnskapet ditt</p>
                  </div>
                </div>
              </div>

              <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {cfoChatHistory.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed ${
                        msg.sender === "user"
                          ? "bg-blue-600 text-white rounded-br-none shadow-xs"
                          : "bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200 shadow-xs whitespace-pre-wrap"
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                ))}
                {cfoLoading && (
                  <div className="text-xs text-slate-400 flex items-center space-x-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Llama 3.1 tenker og analyserer tallene dine...</span>
                  </div>
                )}
              </div>

              <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Spør din CFO om likviditet, skatt, kostnadskutt, eller regnskapsregler..."
                  value={cfoQuestion}
                  onChange={e => setCfoQuestion(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleCfoAsk()}
                  className="flex-1 px-4 py-2.5 text-xs bg-white border border-slate-200 rounded-xl focus:outline-blue-500"
                />
                <button
                  onClick={handleCfoAsk}
                  disabled={cfoLoading}
                  className="p-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl shadow-xs transition-colors cursor-pointer"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* TAB 12: KUNDESERVICE DESK (HUMAN-IN-THE-LOOP) */}
          {activeTab === "support" && (
            <div className="max-w-6xl mx-auto h-[calc(100vh-140px)] grid grid-cols-1 md:grid-cols-3 gap-4 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
              {/* Ticket liste */}
              <div className="border-r border-slate-200 flex flex-col h-full bg-slate-50/50">
                <div className="p-3.5 border-b border-slate-200 font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center justify-between">
                  <span>Henvendelser ({tickets.length})</span>
                  <Headphones className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                  {tickets.map(t => (
                    <div
                      key={t.id}
                      onClick={() => setSelectedTicket(t)}
                      className={`p-3.5 cursor-pointer text-xs transition-colors ${
                        selectedTicket?.id === t.id
                          ? "bg-white border-l-4 border-blue-600 shadow-xs"
                          : "hover:bg-slate-100/70"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">{t.customer_name}</span>
                        <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-semibold">
                          {t.priority}
                        </span>
                      </div>
                      <div className="text-slate-600 font-medium truncate mt-1">{t.subject}</div>
                      <div className="text-slate-400 text-[10px] mt-1">
                        {new Date(t.created_at).toLocaleDateString("nb-NO")}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Chat med kunde & operatørpanel */}
              <div className="col-span-2 flex flex-col h-full bg-white">
                {selectedTicket ? (
                  <>
                    <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm">{selectedTicket.subject}</h4>
                        <p className="text-xs text-slate-500">
                          Fra: {selectedTicket.customer_name} ({selectedTicket.customer_email})
                        </p>
                      </div>
                      <div className="text-xs bg-blue-100 text-blue-800 px-2.5 py-1 rounded-full font-semibold">
                        Ansvarlig operatør: Deg
                      </div>
                    </div>

                    <div className="flex-1 p-4 overflow-y-auto space-y-3">
                      {selectedTicket.messages.map(m => (
                        <div
                          key={m.id}
                          className={`flex ${m.sender === "OPERATOR_YOU" ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-[75%] rounded-2xl p-3 text-xs leading-relaxed ${
                              m.sender === "OPERATOR_YOU"
                                ? "bg-blue-600 text-white rounded-br-none shadow-xs"
                                : m.sender === "LLAMA_AI"
                                ? "bg-purple-50 text-purple-900 border border-purple-200 rounded-bl-none shadow-xs"
                                : "bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200 shadow-xs"
                            }`}
                          >
                            <div className="font-semibold text-[10px] mb-1 opacity-80">{m.sender_name}</div>
                            <div>{m.message}</div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="Skriv direkte svar til kunden som operatør..."
                        value={operatorReply}
                        onChange={e => setOperatorReply(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleSendOperatorReply()}
                        className="flex-1 px-4 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-blue-500"
                      />
                      <button
                        onClick={handleSendOperatorReply}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-xs cursor-pointer flex items-center space-x-1"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Svar kunde</span>
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
                    Velg en henvendelse til venstre for å åpne operatørdialogen.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 13: INNSTILLINGER */}
          {activeTab === "settings" && (
            <div className="max-w-3xl mx-auto space-y-6">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                <h3 className="font-bold text-slate-900 text-base">Bedriftsprofil & Innstillinger</h3>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="block text-slate-500 font-semibold mb-1">Selskapsnavn</label>
                    <input
                      type="text"
                      value={companySettings.company_name}
                      onChange={e => setCompanySettings({ ...companySettings, company_name: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-500 font-semibold mb-1">Organisasjonsnummer</label>
                    <input
                      type="text"
                      value={companySettings.org_number}
                      onChange={e => setCompanySettings({ ...companySettings, org_number: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-500 font-semibold mb-1">Driftskonto (Bankkontonummer)</label>
                    <input
                      type="text"
                      value={companySettings.bank_account}
                      onChange={e => setCompanySettings({ ...companySettings, bank_account: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-500 font-semibold mb-1">E-postadresse</label>
                    <input
                      type="email"
                      value={companySettings.email}
                      onChange={e => setCompanySettings({ ...companySettings, email: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg"
                    />
                  </div>
                </div>
                <button
                  onClick={async () => {
                    await fetch(`${API_BASE}/accounting/settings`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify(companySettings)
                    });
                    alert("Innstillinger lagret!");
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Lagre innstillinger
                </button>
              </div>
            </div>
          )}

          {activeTab === "notifications" && (
            <NotificationsPanel
              apiBase={API_BASE}
              onNavigate={(tab) => setActiveTab(tab as TabType)}
              onCountChange={setNotificationCount}
            />
          )}

          {activeTab === "payroll" && (
            <PayrollPanel apiBase={API_BASE} onPosted={() => void fetchAllData()} />
          )}

          {activeTab === "billing" && (
            <BillingPanel apiBase={API_BASE} onChanged={() => void fetchAllData()} />
          )}

          {activeTab === "archive" && (
            <ArchiveSaftCompliancePanel apiBase={API_BASE} mode="archive" />
          )}

          {activeTab === "saft" && (
            <ArchiveSaftCompliancePanel apiBase={API_BASE} mode="saft" onImported={() => void fetchAllData()} />
          )}

          {activeTab === "compliance" && (
            <ArchiveSaftCompliancePanel apiBase={API_BASE} mode="compliance" />
          )}
        </div>
      </main>

      {showAuthModal && (
        <AuthModal
          apiBase={API_BASE}
          onClose={() => setShowAuthModal(false)}
          onAuthenticated={(u) => {
            setCurrentUser(u);
            void fetchAllData();
          }}
        />
      )}

      {/* --- MODAL 1: FORHÅNDSVISNING AV BILAG (BILDE ELLER PDF) --- */}
      {previewFileUrl && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-4xl w-full h-[85vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-blue-600" />
                <span className="font-bold text-sm text-slate-800">Forhåndsvisning av bilag</span>
              </div>
              <button
                onClick={() => setPreviewFileUrl(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 bg-slate-100 flex items-center justify-center p-4 overflow-auto">
              {previewFileType === "pdf" ? (
                <iframe src={previewFileUrl} className="w-full h-full rounded-xl border border-slate-300" />
              ) : (
                <img
                  src={previewFileUrl}
                  alt="Bilag"
                  className="max-h-full max-w-full object-contain rounded-xl shadow-md border border-slate-200"
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL 2: DETALJER OM BILAG MED POSTERINGSLINJER --- */}
      {selectedVoucherForDetail && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base">
                  Bilag #{selectedVoucherForDetail.voucher_number}
                </h3>
                <p className="text-xs text-slate-500">
                  {new Date(selectedVoucherForDetail.date).toLocaleDateString("nb-NO")} &bull;{" "}
                  {selectedVoucherForDetail.description}
                </p>
              </div>
              <button
                onClick={() => setSelectedVoucherForDetail(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                  <tr>
                    <th className="py-2.5 px-3 text-left">Konto</th>
                    <th className="py-2.5 px-3 text-left">Tekst</th>
                    <th className="py-2.5 px-3 text-right">Debet</th>
                    <th className="py-2.5 px-3 text-right">Kredit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selectedVoucherForDetail.lines.map((l, i) => (
                    <tr key={i}>
                      <td className="p-2.5 font-mono font-bold text-blue-600">{l.account_number}</td>
                      <td className="p-2.5 text-slate-800">{l.description}</td>
                      <td className="p-2.5 text-right font-medium">
                        {l.debit > 0 ? `${l.debit.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK` : "-"}
                      </td>
                      <td className="p-2.5 text-right font-medium">
                        {l.credit > 0 ? `${l.credit.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK` : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedVoucherForDetail.source_document && (
              <div className="pt-2">
                <button
                  onClick={() => {
                    const doc = selectedVoucherForDetail.source_document!;
                    setPreviewFileUrl(`http://localhost:8000${doc}`);
                    setPreviewFileType(doc.endsWith(".pdf") ? "pdf" : "image");
                  }}
                  className="w-full py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs rounded-lg flex items-center justify-center space-x-1.5 transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  <span>Se originalt bilag / vedlegg</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- MODAL 3: OPPRETT SALGSFAKTURA (CONTA FAKTURA MODAL) --- */}
      {showNewInvoiceModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base">Opprett Salgsfaktura (Conta Faktura)</h3>
                <p className="text-xs text-slate-500">
                  Fakturaen bokføres automatisk i hovedboken: Debet 1500, Kredit 3000 & 2700.
                </p>
              </div>
              <button
                onClick={() => setShowNewInvoiceModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Kundenavn</label>
                <input
                  type="text"
                  placeholder="F.eks. Fjord Design Studio AS"
                  value={invCustomerName}
                  onChange={e => setInvCustomerName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Kunde E-post</label>
                <input
                  type="email"
                  placeholder="faktura@kunde.no"
                  value={invCustomerEmail}
                  onChange={e => setInvCustomerEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Forfallsdato</label>
                <input
                  type="date"
                  value={invDueDate}
                  onChange={e => setInvDueDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>
            </div>

            {/* Fakturalinjer */}
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                  <tr>
                    <th className="py-2 px-3 text-left">Vare- / Tjenestelinje</th>
                    <th className="py-2 px-3 text-center w-16">Antall</th>
                    <th className="py-2 px-3 text-right w-24">Enhetspris</th>
                    <th className="py-2 px-3 text-center w-20">MVA %</th>
                    <th className="py-2 px-3 text-right w-24">Sum eks. MVA</th>
                  </tr>
                </thead>
                <tbody>
                  {invLines.map((line, idx) => (
                    <tr key={idx}>
                      <td className="p-2">
                        <input
                          type="text"
                          value={line.description}
                          onChange={e => {
                            const next = [...invLines];
                            next[idx].description = e.target.value;
                            setInvLines(next);
                          }}
                          className="w-full px-2 py-1 border border-slate-200 rounded text-xs"
                        />
                      </td>
                      <td className="p-2 text-center">
                        <input
                          type="number"
                          value={line.quantity}
                          onChange={e => {
                            const q = parseFloat(e.target.value) || 1;
                            const next = [...invLines];
                            next[idx].quantity = q;
                            next[idx].amount = round(q * next[idx].unit_price, 2);
                            setInvLines(next);
                          }}
                          className="w-14 px-1 py-1 border border-slate-200 rounded text-center text-xs"
                        />
                      </td>
                      <td className="p-2 text-right">
                        <input
                          type="number"
                          value={line.unit_price}
                          onChange={e => {
                            const p = parseFloat(e.target.value) || 0;
                            const next = [...invLines];
                            next[idx].unit_price = p;
                            next[idx].amount = round(next[idx].quantity * p, 2);
                            setInvLines(next);
                          }}
                          className="w-24 px-1 py-1 border border-slate-200 rounded text-right text-xs"
                        />
                      </td>
                      <td className="p-2 text-center">25%</td>
                      <td className="p-2 text-right font-bold">
                        {line.amount.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <div className="text-xs text-slate-500">
                Totalbeløp inkl. 25% MVA:{" "}
                <strong className="text-slate-900 text-sm">
                  {round(
                    invLines.reduce((s, l) => s + l.amount, 0) * 1.25,
                    2
                  ).toLocaleString("nb-NO")}{" "}
                  NOK
                </strong>
              </div>
              <button
                onClick={handleCreateCustomerInvoice}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-xs cursor-pointer"
              >
                Opprett og bokfør faktura
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL 4: OPPRETT LEVERANDØR --- */}
      {showNewSupplierModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base">Ny Leverandør</h3>
              <button
                onClick={() => setShowNewSupplierModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              {/* Brreg hurtigoppslag */}
              <div className="bg-blue-50/50 p-2.5 rounded-xl border border-blue-100">
                <label className="block font-semibold text-blue-900 mb-1 flex items-center space-x-1">
                  <Search className="w-3.5 h-3.5 text-blue-600" />
                  <span>Søk i Brønnøysund (automatisk utfylling):</span>
                </label>
                <input
                  type="text"
                  placeholder="Søk firmanavn eller org.nr i Brreg..."
                  onChange={e => handleBrregSearch(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-blue-200 rounded-lg text-xs"
                />
                {brregResults.length > 0 && (
                  <div className="mt-2 bg-white border border-blue-200 rounded-lg max-h-36 overflow-y-auto divide-y divide-slate-100 shadow-sm">
                    {brregResults.slice(0, 5).map(b => (
                      <div
                        key={b.org_number}
                        onClick={() => {
                          setNewSupName(b.name);
                          setNewSupOrgnr(b.org_number);
                          setBrregResults([]);
                        }}
                        className="p-2 hover:bg-blue-50/70 cursor-pointer text-[11px]"
                      >
                        <div className="font-bold text-slate-800">{b.name}</div>
                        <div className="text-slate-500 font-mono text-[10px]">
                          {b.org_number} &bull; {b.city} &bull; {b.is_vat_registered ? "MVA-reg" : "Ikke MVA"}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Leverandørnavn</label>
                <input
                  type="text"
                  placeholder="F.eks. Telenor, Elkjøp, Google..."
                  value={newSupName}
                  onChange={e => setNewSupName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Organisasjonsnummer</label>
                <input
                  type="text"
                  placeholder="9 siffer"
                  value={newSupOrgnr}
                  onChange={e => setNewSupOrgnr(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Bankkontonummer for utbetaling</label>
                <input
                  type="text"
                  placeholder="1234.56.78903"
                  value={newSupBankAcc}
                  onChange={e => setNewSupBankAcc(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Standard kostnadskonto</label>
                <select
                  value={newSupAccount}
                  onChange={e => setNewSupAccount(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                >
                  {accounts
                    .filter(a => a.account_number >= 4000 && a.account_number < 8000)
                    .map(a => (
                      <option key={a.account_number} value={a.account_number}>
                        {a.account_number} - {a.name}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={handleCreateSupplier}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-xs cursor-pointer"
              >
                Lagre leverandør
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL 5: OFFISIELL ALTINN KVITTERING --- */}
      {altinnReceipt && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
                  ✓
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Altinn & Skatteetaten Kvittering</h3>
                  <p className="text-[11px] text-slate-500">MVA-melding levert via Maskinporten</p>
                </div>
              </div>
              <button onClick={() => setAltinnReceipt(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-2 text-xs text-emerald-950">
              <div className="font-semibold text-sm text-emerald-900">{altinnReceipt.message}</div>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-emerald-200/60 font-mono text-[11px]">
                <div>
                  <span className="text-emerald-700 block text-[10px]">Arkivreferanse:</span>
                  <strong>{altinnReceipt.altinn_archive_reference}</strong>
                </div>
                <div>
                  <span className="text-emerald-700 block text-[10px]">Innsendings-ID:</span>
                  <strong>{altinnReceipt.submission_id}</strong>
                </div>
              </div>
            </div>

            <div className="border border-slate-200 rounded-xl p-3.5 space-y-2 text-xs">
              <div className="font-bold text-slate-900">Betalingsinformasjon for MVA:</div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-slate-500 block">Konto for innbetaling:</span>
                  <span className="font-mono font-semibold">{altinnReceipt.payment_info?.kontonummer}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">KID-nummer:</span>
                  <span className="font-mono font-semibold">{altinnReceipt.payment_info?.kid}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Forfallsdato:</span>
                  <span className="font-semibold">{altinnReceipt.payment_info?.forfallsdato}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Beløp å betale:</span>
                  <span className="font-bold text-slate-900">
                    {altinnReceipt.figures?.netto_mva_aa_betale?.toLocaleString("nb-NO")} NOK
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setAltinnReceipt(null)}
                className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-xl shadow-xs cursor-pointer"
              >
                Lukk kvittering
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
