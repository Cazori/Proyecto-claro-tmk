import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Components
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatArea from './components/chat/ChatArea';
import Dashboard from './components/dashboard/Dashboard';
import InventoryUpload from './components/upload/InventoryUpload';
import FichasGrid from './components/fichas/FichasGrid';
import ExpertKnowledge from './components/expert/ExpertKnowledge';
import ImageModal from './components/common/ImageModal';

// Services
import { chatService } from './services/api';

const ChatApp = () => {
  // State
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hola. Soy Cleo. Tu sistema de inventario está en línea.",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isSidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
  const [activeTab, setActiveTab] = useState('chat');
  const [file, setFile] = useState(null);
  const [specFile, setSpecFile] = useState(null);
  const [specName, setSpecName] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const [specUploadStatus, setSpecUploadStatus] = useState('');
  const [knowledge, setKnowledge] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({
    lastUpdate: 'Hoy',
    totalItems: 0,
    criticalStock: 0
  });
  const [specsList, setSpecsList] = useState([]);
  const [specsMapping, setSpecsMapping] = useState({});
  const [fichasSearch, setFichasSearch] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);

  const chatEndRef = useRef(null);

  // Effects
  useEffect(() => {
    const scrollToBottom = () => {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };
    scrollToBottom();
  }, [messages, activeTab]);

  useEffect(() => {
    const handleResize = () => {
      setSidebarOpen(window.innerWidth > 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [knowledgeData, specsData, mappingData, inventoryMeta] = await Promise.all([
          chatService.getKnowledge(),
          chatService.getSpecsList(),
          chatService.getSpecsMapping(),
          chatService.getInventoryMetadata()
        ]);
        setKnowledge(knowledgeData);
        setSpecsList(specsData);
        setSpecsMapping(mappingData);

        if (inventoryMeta && inventoryMeta.last_update) {
          const date = new Date(inventoryMeta.last_update);
          const day = date.getDate();
          const month = date.toLocaleString('es-ES', { month: 'long' });
          const dynamicText = `Hola. Soy Cleo. Tu sistema de inventario está en línea, inventario actualizado al día ${day} de ${month}.`;
          setMessages(prev => prev.map(m => m.id === 1 ? { ...m, text: dynamicText } : m));
        }
      } catch (e) {
        console.error("Error loading initial data", e);
      }
    };
    loadInitialData();
  }, []);

  // Handlers
  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { id: Date.now(), text: input, sender: 'user', timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    const loadingId = Date.now() + 1;
    setMessages(prev => [...prev, {
      id: loadingId,
      text: "Procesando consulta...",
      sender: 'bot',
      timestamp: new Date(),
      loading: true
    }]);

    try {
      const data = await chatService.sendMessage(input);
      setMessages(prev => prev.map(msg =>
        msg.id === loadingId
          ? { ...msg, text: data.response, loading: false }
          : msg
      ));
    } catch (error) {
      setMessages(prev => prev.map(msg =>
        msg.id === loadingId
          ? { ...msg, text: "Error de conexión con el servidor. Intenta de nuevo.", loading: false }
          : msg
      ));
    }
  };

  const handleFileUpload = async () => {
    if (!file) return;
    setUploadStatus('Subiendo y procesando con IA... (Esto puede tardar unos segundos)');

    try {
      const response = await chatService.uploadInventory(file);
      if (response.ok) {
        setUploadStatus('¡Inventario procesado con éxito! Cleo ya tiene los datos actualizados.');
        setFile(null);
        // Refresh metadata and stats to show the new date
        const inventoryMeta = await chatService.getInventoryMetadata();
        if (inventoryMeta && inventoryMeta.last_update) {
          const date = new Date(inventoryMeta.last_update);
          const day = date.getDate();
          const month = date.toLocaleString('es-ES', { month: 'long' });
          const dynamicText = `Hola. Soy Cleo. Tu sistema de inventario está en línea, inventario actualizado al día ${day} de ${month}.`;
          setMessages(prev => prev.map(m => m.id === 1 ? { ...m, text: dynamicText } : m));
        }
        fetchStats();
      } else {
        setUploadStatus('Error en la carga. Asegúrate de que es un PDF válido.');
      }
    } catch (error) {
      setUploadStatus('Error de conexión o tiempo excedido.');
    }
  };

  const handleSpecUpload = async () => {
    if (!specFile || !specName) return;
    setSpecUploadStatus('Subiendo ficha...');

    try {
      // RENAME logic: Create a new file object with the desired name
      const extension = specFile.name.split('.').pop();
      const newFileName = `${specName.trim()}.${extension}`;
      const renamedFile = new File([specFile], newFileName, { type: specFile.type });

      const data = await chatService.uploadSpec(renamedFile);
      setSpecUploadStatus(data.message);
      setSpecFile(null);
      setSpecName(''); // Clear name
      const knowledgeData = await chatService.getKnowledge();
      setKnowledge(knowledgeData);

      // Refresh specs list to show the new file
      const specsData = await chatService.getSpecsList();
      setSpecsList(specsData);
    } catch (error) {
      setSpecUploadStatus('Error de conexión.');
    }
  };

  const fetchStats = () => {
    setDashboardStats({
      lastUpdate: new Date().toLocaleTimeString(),
      totalItems: 182,
      criticalStock: 12
    });
  };

  const handleViewSpec = (materialId, modelName) => {
    // Priority 1: Use the robust mapping from backend
    const matId = String(materialId);
    let found = specsMapping[matId];

    if (!found) {
      // Priority 2: Match by exact Material ID anywhere in the filename (local fallback)
      found = specsList.find(f => f.includes(matId));
    }

    if (!found && modelName) {
      // Priority 3: Match by model name
      const search = modelName.toLowerCase().replace(/[\s-]/g, '');
      found = specsList.find(filename => {
        const cleanFile = filename.toLowerCase().replace(/[\s-]/g, '').split('(')[0].replace(/\.[^/.]+$/, "");
        return cleanFile.includes(search) || search.includes(cleanFile);
      });
    }

    if (found) {
      setSelectedImage(chatService.getSpecImageUrl(found));
    } else if (modelName) {
      const search = modelName.toLowerCase().replace(/[\s-]/g, '');
      const keywords = search.split(/\s+/).filter(k => k.length > 2);
      if (keywords.length > 0) {
        const partialMatch = specsList.find(filename => {
          const f = filename.toLowerCase();
          return keywords.every(k => f.includes(k));
        });
        if (partialMatch) setSelectedImage(chatService.getSpecImageUrl(partialMatch));
      }
    }
  };

  return (
    <div className="app-container">
      {/* Mobile Overlay */}
      <div
        className={`sidebar-overlay ${isSidebarOpen && window.innerWidth <= 768 ? 'active' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <Sidebar
        isSidebarOpen={isSidebarOpen}
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          if (window.innerWidth <= 768) setSidebarOpen(false);
        }}
      />

      <main className="main-content">
        <Header
          activeTab={activeTab}
          isSidebarOpen={isSidebarOpen}
          setSidebarOpen={setSidebarOpen}
        />

        <div className="chat-area-container" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {activeTab === 'chat' && (
            <ChatArea
              messages={messages}
              chatEndRef={chatEndRef}
              input={input}
              setInput={setInput}
              handleSend={handleSend}
              specsList={specsList}
              specsMapping={specsMapping}
              onViewSpec={handleViewSpec}
            />
          )}

          {activeTab === 'dashboard' && (
            <Dashboard stats={dashboardStats} />
          )}

          {activeTab === 'upload' && (
            <InventoryUpload
              file={file}
              setFile={setFile}
              handleFileUpload={handleFileUpload}
              uploadStatus={uploadStatus}
            />
          )}

          {activeTab === 'fichas' && (
            <FichasGrid
              fichasSearch={fichasSearch}
              setFichasSearch={setFichasSearch}
              specsList={specsList}
              setSelectedImage={setSelectedImage}
            />
          )}

          {activeTab === 'expert' && (
            <ExpertKnowledge
              specFile={specFile}
              setSpecFile={setSpecFile}
              specName={specName}
              setSpecName={setSpecName}
              handleSpecUpload={handleSpecUpload}
              specUploadStatus={specUploadStatus}
              knowledge={knowledge}
            />
          )}
        </div>
      </main>

      <ImageModal
        imageUrl={selectedImage}
        onClose={() => setSelectedImage(null)}
      />
    </div>
  );
};

export default ChatApp;
