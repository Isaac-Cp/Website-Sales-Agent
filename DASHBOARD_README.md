
# SalesAgent Pro Dashboard v2.0

The SalesAgent Pro Dashboard is a modern, real-time interface for monitoring and managing your automated outreach campaigns.

## Architecture

The dashboard follows a modular architecture:

-   **Backend**: Powered by **FastAPI** for high-performance API endpoints and **WebSockets** for real-time logs.
-   **Service Layer**: `dashboard_service.py` handles database queries, data aggregation, and includes a built-in caching mechanism (30-second TTL) to optimize performance.
-   **Frontend**: A single-page application built with:
    -   **Tailwind CSS**: For responsive, modern styling.
    -   **Alpine.js**: For lightweight reactive state management.
    -   **Chart.js**: For interactive data visualization (Outreach Activity & Status Distribution).
    -   **Lucide Icons**: For clear, accessible iconography.

## Key Features

-   **Real-time Metrics**: Track total leads, emails sent today, replies, and success rates.
-   **Data Visualization**:
    -   **Outreach Activity**: Line chart showing daily email volume.
    -   **Status Distribution**: Doughnut chart visualizing the lead funnel.
-   **Live System Logs**: WebSocket-powered log feed showing system activity in real-time.
-   **Lead Funnel**: Visual representation of lead progression from "scraped" to "sale closed".
-   **Recent Activity**: A detailed table of the latest email events.
-   **Accessibility**: WCAG 2.1 AA compliant UI components with proper ARIA labels and roles.

## Performance

The dashboard is optimized for a sub-2-second load time by:
-   Using CDN-hosted assets for faster delivery.
-   Implementing backend caching to reduce database overhead.
-   Utilizing asynchronous API calls for data fetching.

## Security

-   **API Key Authentication**: Secure access to dashboard data via the `X-API-Key` header.
-   **Configurable**: Set your `DASHBOARD_API_KEY` in the `.env` file.

## Testing

Comprehensive test suite in `test_dashboard.py` covers:
-   Statistic aggregation logic.
-   Caching mechanisms.
-   Funnel reconstruction.
-   Daily volume calculation.

To run tests:
```bash
python test_dashboard.py
```

## Deployment

The dashboard is integrated into the main application. To start the web server:
```bash
python main.py --serve
```
The dashboard will be available at `http://localhost:8000/`.
