import { useMemo } from 'react';
import Fuse from 'fuse.js';

/**
 * Hook for fuzzy searching a dataset using Fuse.js
 * @param {Array} data - The array of items to search through
 * @param {Object} options - Fuse.js options
 */
const useFuzzySearch = (data, options = {}) => {
    const defaultOptions = {
        threshold: 0.3,
        location: 0,
        distance: 100,
        minMatchCharLength: 2,
        keys: ['name'],
        ...options
    };

    const fuse = useMemo(() => {
        if (!data || data.length === 0) return null;
        return new Fuse(data, defaultOptions);
    }, [data, defaultOptions]);

    const search = (query) => {
        if (!fuse || !query) return [];
        return fuse.search(query).map(result => result.item);
    };

    return { search };
};

export default useFuzzySearch;
