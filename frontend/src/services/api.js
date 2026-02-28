const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const chatService = {
    async sendMessage(query) {
        const response = await fetch(`${BASE_URL}/chat?query=${encodeURIComponent(query)}`);
        return response.json();
    },

    async uploadInventory(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${BASE_URL}/upload-inventory`, {
            method: 'POST',
            body: formData
        });
        return response;
    },

    async uploadSpec(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${BASE_URL}/upload-spec`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    },

    async getKnowledge() {
        const response = await fetch(`${BASE_URL}/knowledge`);
        return response.json();
    },

    async getSpecsList() {
        const response = await fetch(`${BASE_URL}/specs-list`);
        return response.json();
    },

    async getSpecsMapping() {
        const response = await fetch(`${BASE_URL}/specs-mapping`);
        return response.json();
    },

    async getInventoryMetadata() {
        const response = await fetch(`${BASE_URL}/inventory-metadata`);
        return response.json();
    },

    async getQuotas() {
        const response = await fetch(`${BASE_URL}/quotas`);
        return response.json();
    },

    async uploadQuotas(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${BASE_URL}/upload-quotas`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    },

    async findProduct(material) {
        const response = await fetch(`${BASE_URL}/find-product?material=${encodeURIComponent(material)}`);
        return response.json();
    },

    async generateTip(model, specs) {
        const response = await fetch(`${BASE_URL}/generate-tip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model, specs })
        });
        return response.json();
    },

    async updateKnowledge(entry) {
        const response = await fetch(`${BASE_URL}/update-knowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry)
        });
        return response.json();
    },

    async applyAutoTips(category, tip) {
        const response = await fetch(`${BASE_URL}/apply-auto-tips`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, tip })
        });
        return response.json();
    },

    async linkSpec(materialId, filename) {
        const response = await fetch(`${BASE_URL}/link-spec`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ material_id: materialId, filename: filename })
        });
        return response.json();
    },

    getSpecImageUrl(filename) {
        return `${BASE_URL}/specs/${filename}`;
    }
};
