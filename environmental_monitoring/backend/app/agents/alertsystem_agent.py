"""
AlertSystem Agent - Real-time alerting and reporting system

This agent is responsible for:
- Monitoring environmental events and anomalies
- Sending alerts via multiple channels (email, SMS, webhooks)
- Generating reports and notifications
- Managing alert subscriptions and preferences
- Escalating critical alerts
- Providing alert history and analytics
"""

import asyncio
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

from app.services.database import (
    get_active_alerts,
)
from app.models.models import EnvironmentalEvent
from app.schemas.schemas import AlertCreate

logger = logging.getLogger(__name__)

class AlertSystemAgent:
    """Agent for real-time alerting and reporting."""

    def __init__(self):
        self.alert_channels: Dict[str, Any] = {}
        self.subscriptions: Dict[str, List[str]] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def initialize(self):
        """Initialize the AlertSystem agent."""
        logger.info("🚨 Initializing AlertSystem Agent...")

        # Configure alert channels
        await self._configure_alert_channels()

        # Load alert subscriptions
        await self._load_subscriptions()

        # Start alert monitoring
        await self.start_alert_monitoring()

        logger.info("✅ AlertSystem Agent initialized")

    async def cleanup(self):
        """Cleanup agent resources."""
        logger.info("🧹 Cleaning up AlertSystem Agent...")

        self.running = False

        # Cancel all running tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # Close HTTP client
        await self.http_client.aclose()

        logger.info("✅ AlertSystem Agent cleanup complete")

    async def _configure_alert_channels(self):
        """Configure alert notification channels."""
        # Email configuration
        self.alert_channels["email"] = {
            "enabled": True,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "alerts@environmental-monitor.com",  # Would be from env/config
            "password": "dummy_password",  # Would be from secure config
            "from_email": "alerts@environmental-monitor.com"
        }

        # SMS configuration (Twilio)
        self.alert_channels["sms"] = {
            "enabled": True,
            "account_sid": "dummy_sid",  # From env
            "auth_token": "dummy_token",  # From env
            "from_number": "+1234567890"
        }

        # Webhook configuration
        self.alert_channels["webhook"] = {
            "enabled": True,
            "urls": [
                "https://api.external-service.com/webhooks/alerts",
                "https://dashboard.company.com/api/alerts"
            ]
        }

        # Slack configuration
        self.alert_channels["slack"] = {
            "enabled": True,
            "webhook_url": "https://hooks.slack.com/services/dummy/webhook",  # From env
            "channel": "#environmental-alerts"
        }

        logger.info("📡 Alert channels configured")

    async def _load_subscriptions(self):
        """Load alert subscriptions."""
        # Sample subscriptions - in production, this would come from database
        self.subscriptions = {
            "critical_alerts": [
                "admin@company.com",
                "+1234567890",  # SMS
                "https://api.external-service.com/alerts"
            ],
            "anomaly_alerts": [
                "scientists@company.com",
                "#environmental-alerts"  # Slack
            ],
            "maintenance_alerts": [
                "maintenance@company.com"
            ],
            "daily_reports": [
                "management@company.com",
                "stakeholders@company.com"
            ]
        }

        logger.info("📋 Alert subscriptions loaded")

    async def start_alert_monitoring(self):
        """Start alert monitoring and processing."""
        if self.running:
            return

        self.running = True
        logger.info("🚀 Starting alert monitoring system...")

        # Start alert processing task
        alert_task = asyncio.create_task(self._process_alerts())
        self.tasks.append(alert_task)

        # Start report generation task
        report_task = asyncio.create_task(self._generate_reports())
        self.tasks.append(report_task)

        # Start alert escalation task
        escalation_task = asyncio.create_task(self._monitor_alert_escalation())
        self.tasks.append(escalation_task)

    async def _process_alerts(self):
        """Process and send alerts for environmental events."""
        while self.running:
            try:
                # Check for new alerts to process
                await self._check_and_send_alerts()

                # Wait for next check cycle (5 minutes)
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"❌ Error processing alerts: {e}")
                await asyncio.sleep(60)

    async def _check_and_send_alerts(self):
        """Check for new alerts and send notifications."""
        # Get active alerts that haven't been sent
        active_alerts = await get_active_alerts()

        for alert_event in active_alerts:
            try:
                # Check if we've already sent alerts for this event
                if await self._should_send_alert(alert_event):
                    # Determine alert type and recipients
                    alert_type, recipients = self._determine_alert_type_and_recipients(alert_event)

                    # Send alerts via configured channels
                    await self._send_alert_notifications(alert_event, alert_type, recipients)

                    # Mark alert as sent (in production, this would update database)
                    logger.info(f"✅ Alert sent for event: {alert_event.title}")

            except Exception as e:
                logger.error(f"❌ Error sending alert for event {alert_event.id}: {e}")

    async def _should_send_alert(self, alert_event: EnvironmentalEvent) -> bool:
        """Determine if an alert should be sent for this event."""
        # Check if alert was created recently (within last 10 minutes)
        time_since_creation = datetime.utcnow() - alert_event.timestamp
        return time_since_creation.total_seconds() < 600  # 10 minutes

    def _determine_alert_type_and_recipients(self, alert_event: EnvironmentalEvent) -> Tuple[str, List[str]]:
        """Determine alert type and recipients based on event."""
        alert_type = "general_alerts"

        if alert_event.severity == "critical":
            alert_type = "critical_alerts"
        elif alert_event.event_type == "anomaly":
            alert_type = "anomaly_alerts"
        elif "maintenance" in alert_event.title.lower():
            alert_type = "maintenance_alerts"

        recipients = self.subscriptions.get(alert_type, [])
        return alert_type, recipients

    async def _send_alert_notifications(self, alert_event: EnvironmentalEvent,
                                      alert_type: str, recipients: List[str]):
        """Send alert notifications via configured channels."""
        alert_subject = f"Environmental Alert: {alert_event.title}"
        alert_message = self._format_alert_message(alert_event)

        for recipient in recipients:
            try:
                if "@" in recipient:  # Email
                    await self._send_email_alert(recipient, alert_subject, alert_message)
                elif recipient.startswith("+"):  # SMS
                    await self._send_sms_alert(recipient, alert_message)
                elif recipient.startswith("http"):  # Webhook
                    await self._send_webhook_alert(recipient, alert_event)
                elif recipient.startswith("#"):  # Slack
                    await self._send_slack_alert(recipient, alert_subject, alert_message)

            except Exception as e:
                logger.error(f"❌ Failed to send alert to {recipient}: {e}")

    def _format_alert_message(self, alert_event: EnvironmentalEvent) -> str:
        """Format alert message for notifications."""
        return f"""
ENVIRONMENTAL MONITORING ALERT

Event: {alert_event.title}
Severity: {alert_event.severity.upper()}
Type: {alert_event.event_type}

Description: {alert_event.description or 'No description available'}

Location: {f'Lat: {alert_event.latitude}, Lon: {alert_event.longitude}' if alert_event.latitude else 'Location not specified'}

Time: {alert_event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Please take appropriate action based on the severity level.

Environmental Monitoring System
"""

    async def _send_email_alert(self, recipient: str, subject: str, message: str):
        """Send email alert."""
        email_config = self.alert_channels.get("email", {})
        if not email_config.get("enabled", False):
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = email_config["from_email"]
            msg['To'] = recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            # In production, this would actually send the email
            # For demo purposes, we just log it
            logger.info(f"📧 Email alert sent to {recipient}: {subject}")

        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")

    async def _send_sms_alert(self, recipient: str, message: str):
        """Send SMS alert via Twilio."""
        sms_config = self.alert_channels.get("sms", {})
        if not sms_config.get("enabled", False):
            return

        try:
            # In production, this would use Twilio SDK
            # For demo purposes, we just log it
            logger.info(f"📱 SMS alert sent to {recipient}: {message[:50]}...")

        except Exception as e:
            logger.error(f"❌ Failed to send SMS alert: {e}")

    async def _send_webhook_alert(self, webhook_url: str, alert_event: EnvironmentalEvent):
        """Send webhook alert."""
        try:
            payload = {
                "event_id": alert_event.id,
                "event_type": alert_event.event_type,
                "severity": alert_event.severity,
                "title": alert_event.title,
                "description": alert_event.description,
                "location": {
                    "latitude": alert_event.latitude,
                    "longitude": alert_event.longitude
                } if alert_event.latitude else None,
                "timestamp": alert_event.timestamp.isoformat(),
                "metadata": alert_event.metadata
            }

            response = await self.http_client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            logger.info(f"🔗 Webhook alert sent to {webhook_url}")

        except Exception as e:
            logger.error(f"❌ Failed to send webhook alert to {webhook_url}: {e}")

    async def _send_slack_alert(self, channel: str, subject: str, message: str):
        """Send Slack alert."""
        slack_config = self.alert_channels.get("slack", {})
        if not slack_config.get("enabled", False):
            return

        try:
            payload = {
                "channel": channel,
                "text": f"*{subject}*\n{message}",
                "username": "Environmental Monitor",
                "icon_emoji": ":warning:"
            }

            # In production, this would post to Slack webhook
            # For demo purposes, we just log it
            logger.info(f"💬 Slack alert sent to {channel}: {subject}")

        except Exception as e:
            logger.error(f"❌ Failed to send Slack alert: {e}")

    async def _generate_reports(self):
        """Generate periodic reports."""
        while self.running:
            try:
                # Generate daily report
                await self._generate_daily_report()

                # Wait for next report cycle (24 hours)
                await asyncio.sleep(86400)

            except Exception as e:
                logger.error(f"❌ Error generating reports: {e}")
                await asyncio.sleep(3600)

    async def _generate_daily_report(self):
        """Generate daily environmental monitoring report."""
        try:
            # Get yesterday's date
            yesterday = datetime.utcnow() - timedelta(days=1)
            report_date = yesterday.strftime('%Y-%m-%d')

            # Gather report data
            report_data = await self._gather_report_data(yesterday)

            # Format report
            report_content = self._format_daily_report(report_data, report_date)

            # Send report to subscribers
            await self._send_daily_report(report_content, report_date)

            logger.info(f"📊 Daily report generated for {report_date}")

        except Exception as e:
            logger.error(f"❌ Failed to generate daily report: {e}")

    async def _gather_report_data(self, report_date: datetime) -> Dict[str, Any]:
        """Gather data for the daily report."""
        # In production, this would query the database for actual metrics
        return {
            "total_readings": 1440,  # Mock data
            "anomalies_detected": 3,
            "alerts_sent": 5,
            "system_uptime": "99.9%",
            "sensor_status": {
                "active": 3,
                "inactive": 0,
                "maintenance": 0
            },
            "environmental_metrics": {
                "avg_temperature": 15.2,
                "avg_humidity": 65.4,
                "air_quality_index": 42,
                "water_quality_ph": 7.1
            }
        }

    def _format_daily_report(self, data: Dict[str, Any], report_date: str) -> str:
        """Format the daily report content."""
        return f"""
ENVIRONMENTAL MONITORING DAILY REPORT - {report_date}

SYSTEM STATUS
=============
Total Sensor Readings: {data['total_readings']}
System Uptime: {data['system_uptime']}

SENSOR STATUS
=============
Active Sensors: {data['sensor_status']['active']}
Inactive Sensors: {data['sensor_status']['inactive']}
Maintenance: {data['sensor_status']['maintenance']}

ENVIRONMENTAL METRICS
=====================
Average Temperature: {data['environmental_metrics']['avg_temperature']}°C
Average Humidity: {data['environmental_metrics']['avg_humidity']}%
Air Quality Index: {data['environmental_metrics']['air_quality_index']}
Water Quality (pH): {data['environmental_metrics']['water_quality_ph']}

ALERTS & ANOMALIES
==================
Anomalies Detected: {data['anomalies_detected']}
Alerts Sent: {data['alerts_sent']}

This report was automatically generated by the Environmental Monitoring System.
For detailed analysis, please visit the monitoring dashboard.
"""

    async def _send_daily_report(self, report_content: str, report_date: str):
        """Send the daily report to subscribers."""
        recipients = self.subscriptions.get("daily_reports", [])

        for recipient in recipients:
            try:
                subject = f"Daily Environmental Report - {report_date}"
                await self._send_email_alert(recipient, subject, report_content)
            except Exception as e:
                logger.error(f"❌ Failed to send daily report to {recipient}: {e}")

    async def _monitor_alert_escalation(self):
        """Monitor and escalate unresolved critical alerts."""
        while self.running:
            try:
                # Check for alerts that need escalation
                await self._check_alert_escalation()

                # Wait for next escalation check (1 hour)
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"❌ Error in alert escalation: {e}")
                await asyncio.sleep(300)

    async def _check_alert_escalation(self):
        """Check for alerts that need escalation."""
        # Get active alerts older than 2 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=2)
        active_alerts = await get_active_alerts()

        escalated_alerts = []
        for alert in active_alerts:
            if alert.timestamp < cutoff_time and alert.severity == "critical":
                escalated_alerts.append(alert)

        # Escalate critical alerts
        for alert in escalated_alerts:
            try:
                await self._escalate_alert(alert)
                logger.warning(f"🚨 Escalated critical alert: {alert.title}")
            except Exception as e:
                logger.error(f"❌ Failed to escalate alert {alert.id}: {e}")

    async def _escalate_alert(self, alert: EnvironmentalEvent):
        """Escalate a critical alert."""
        escalation_message = f"""
CRITICAL ALERT ESCALATION

The following critical alert has been unresolved for more than 2 hours:

{self._format_alert_message(alert)}

IMMEDIATE ATTENTION REQUIRED

This is an automated escalation from the Environmental Monitoring System.
"""

        # Send to escalation recipients (management, emergency contacts)
        escalation_recipients = [
            "emergency@company.com",
            "+1987654321",  # Emergency SMS
            "#emergency-alerts"  # Emergency Slack channel
        ]

        for recipient in escalation_recipients:
            try:
                subject = f"CRITICAL ALERT ESCALATION: {alert.title}"
                if "@" in recipient:
                    await self._send_email_alert(recipient, subject, escalation_message)
                elif recipient.startswith("+"):
                    await self._send_sms_alert(recipient, f"CRITICAL ESCALATION: {alert.title}")
                elif recipient.startswith("#"):
                    await self._send_slack_alert(recipient, subject, escalation_message)
            except Exception as e:
                logger.error(f"❌ Failed to send escalation to {recipient}: {e}")

    async def create_manual_alert(self, alert_data: AlertCreate) -> int:
        """Create a manual alert."""
        # In production, this would save to database
        logger.info(f"📝 Manual alert created: {alert_data.subject}")
        return 999  # Mock ID

    async def get_alert_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get alert history for the specified number of days."""
        # Mock alert history
        return [
            {
                "id": 1,
                "event_type": "anomaly",
                "severity": "medium",
                "title": "Temperature Anomaly Detected",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "status": "resolved"
            },
            {
                "id": 2,
                "event_type": "alert",
                "severity": "high",
                "title": "Air Quality Alert",
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "status": "active"
            }
        ]

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        return {
            "total_alerts_today": 5,
            "critical_alerts": 1,
            "resolved_alerts": 3,
            "active_alerts": 2,
            "average_response_time": "45 minutes",
            "alerts_by_type": {
                "anomaly": 3,
                "maintenance": 1,
                "system": 1
            }
        }

# Global AlertSystem agent instance
alertsystem_agent = AlertSystemAgent()