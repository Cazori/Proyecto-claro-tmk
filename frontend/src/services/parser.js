export const parseMarkdownTable = (text) => {
    const lines = text.trim().split('\n');
    if (lines.length < 3) return null;

    // Find the header row and separator row
    let headerIndex = -1;
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('|') && lines[i + 1] && lines[i + 1].includes('|') && lines[i + 1].includes('---')) {
            headerIndex = i;
            break;
        }
    }

    if (headerIndex === -1) return null;

    const headers = lines[headerIndex]
        .split('|')
        .map(h => h.trim())
        .filter(h => h !== '');

    const dataRows = lines.slice(headerIndex + 2)
        .filter(line => line.includes('|'))
        .map(line => {
            // Robust parsing: remove leading/trailing pipes then split
            const cleanLine = line.trim().replace(/^\||\|$/g, '');
            const values = cleanLine.split('|').map(v => v.trim());

            const obj = {};
            headers.forEach((header, index) => {
                // Map common headers to our expected keys
                let key = header.toLowerCase();
                const val = values[index] !== undefined ? values[index] : '';

                if (key.includes('ref') || key.includes('material')) key = 'Material';
                else if (key.includes('mod')) key = 'Subproducto';
                else if (key.includes('pre')) key = 'Precio Contado';
                else if (key.includes('uni') || key.includes('stoc') || key.includes('cant')) key = 'CantDisponible';
                else if (key.includes('marc')) key = 'Marca';
                else if (key.includes('caract')) key = 'Caracteristicas';
                else if (key.includes('fich')) {
                    key = 'hasSpec';
                    obj[key] = val.toUpperCase() === 'SI';
                    return;
                }
                else if (key.includes('imag')) {
                    key = 'hasImage';
                    obj[key] = val.toUpperCase() === 'VER';
                    return;
                }
                else if (key.includes('tip')) {
                    key = 'tip';
                }

                obj[key] = val;
            });
            return obj;
        });

    return {
        beforeTable: lines.slice(0, headerIndex).join('\n'),
        products: dataRows,
        afterTable: lines.slice(headerIndex + 2 + dataRows.length).join('\n')
    };
};
