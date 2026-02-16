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

    getSpecImageUrl(filename) {
        return `${BASE_URL}/specs/${filename}`;
    }
};
