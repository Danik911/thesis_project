/**
 * API base URL utility for MES Agentic BI (standalone, no auth).
 */

export function getApiBaseUrl(): string {
    const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (configuredBaseUrl !== undefined) {
        if (configuredBaseUrl === '') {
            return configuredBaseUrl;
        }

        if (typeof window !== 'undefined') {
            try {
                const parsedUrl = new URL(configuredBaseUrl);
                const isLocalhostTarget = ['localhost', '127.0.0.1'].includes(parsedUrl.hostname);
                const isIpHostedFrontend = !['localhost', '127.0.0.1'].includes(window.location.hostname);

                if (isLocalhostTarget && isIpHostedFrontend) {
                    parsedUrl.hostname = window.location.hostname;
                    parsedUrl.protocol = window.location.protocol;
                    return parsedUrl.toString().replace(/\/$/, '');
                }
            } catch {
                return configuredBaseUrl;
            }
        }

        return configuredBaseUrl;
    }

    if (typeof window !== 'undefined') {
        return `${window.location.protocol}//${window.location.hostname}:8080`;
    }

    return 'http://localhost:8080';
}
