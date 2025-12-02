"""
CloudWatch Metrics Service for notification system monitoring.

This service publishes metrics to AWS CloudWatch for:
- Notification volume tracking
- Delivery success/failure rates
- Cost tracking (especially for SMS)
- Performance metrics (latency, queue depth)
- Error rates and types

Usage:
    from core.services.metrics_service import MetricsService

    # Track notification creation
    MetricsService.track_notification_created(
        priority='URGENT',
        category='repair_status'
    )

    # Track delivery success
    MetricsService.track_delivery_success(
        channel='email',
        notification_id=123
    )

    # Track delivery failure
    MetricsService.track_delivery_failure(
        channel='sms',
        error_type='InvalidPhone',
        notification_id=456
    )
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for publishing notification metrics to AWS CloudWatch.

    Metrics are organized into namespaces:
    - RS_Systems/Notifications/Volume
    - RS_Systems/Notifications/Delivery
    - RS_Systems/Notifications/Cost
    - RS_Systems/Notifications/Performance
    """

    # CloudWatch namespace
    NAMESPACE = 'RS_Systems/Notifications'

    # Metric names
    METRIC_NOTIFICATION_CREATED = 'NotificationCreated'
    METRIC_NOTIFICATION_DELIVERED = 'NotificationDelivered'
    METRIC_NOTIFICATION_FAILED = 'NotificationFailed'
    METRIC_DELIVERY_LATENCY = 'DeliveryLatency'
    METRIC_SMS_COST = 'SMSCost'
    METRIC_QUEUE_DEPTH = 'QueueDepth'
    METRIC_ERROR_RATE = 'ErrorRate'

    @staticmethod
    def _publish_metric(
        metric_name: str,
        value: float,
        unit: str = 'Count',
        dimensions: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish a metric to CloudWatch.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (Count, Seconds, None, etc.)
            dimensions: Optional dimensions for filtering (e.g., {'Channel': 'email'})

        Returns:
            True if metric was published successfully, False otherwise
        """
        # Skip in development if CloudWatch is not configured
        if not getattr(settings, 'AWS_CLOUDWATCH_ENABLED', False):
            logger.debug(
                f"CloudWatch disabled - would publish: {metric_name}={value} "
                f"({unit}) {dimensions or {}}"
            )
            return True

        try:
            import boto3
            from botocore.exceptions import ClientError

            cloudwatch = boto3.client(
                'cloudwatch',
                region_name=getattr(settings, 'AWS_REGION', 'us-east-1'),
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            )

            # Build metric data
            metric_data = {
                'MetricName': metric_name,
                'Value': float(value),
                'Unit': unit,
                'Timestamp': timezone.now()
            }

            # Add dimensions if provided
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': key, 'Value': str(val)}
                    for key, val in dimensions.items()
                ]

            # Publish to CloudWatch
            cloudwatch.put_metric_data(
                Namespace=MetricsService.NAMESPACE,
                MetricData=[metric_data]
            )

            logger.debug(
                f"Published metric: {metric_name}={value} ({unit}) "
                f"{dimensions or {}}"
            )
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(
                f"CloudWatch ClientError publishing {metric_name}: "
                f"{error_code} - {e.response['Error']['Message']}"
            )
            return False

        except Exception as e:
            logger.exception(f"Error publishing metric {metric_name}: {e}")
            return False

    @staticmethod
    def track_notification_created(
        priority: str,
        category: str,
        recipient_type: Optional[str] = None
    ) -> bool:
        """
        Track notification creation.

        Args:
            priority: Notification priority (URGENT, HIGH, MEDIUM, LOW)
            category: Notification category (repair_status, assignment, etc.)
            recipient_type: Optional recipient type (technician, customer)

        Returns:
            True if metric was published successfully
        """
        dimensions = {
            'Priority': priority,
            'Category': category
        }

        if recipient_type:
            dimensions['RecipientType'] = recipient_type

        return MetricsService._publish_metric(
            metric_name=MetricsService.METRIC_NOTIFICATION_CREATED,
            value=1,
            unit='Count',
            dimensions=dimensions
        )

    @staticmethod
    def track_delivery_success(
        channel: str,
        notification_id: int,
        latency_seconds: Optional[float] = None
    ) -> bool:
        """
        Track successful notification delivery.

        Args:
            channel: Delivery channel (email, sms, in_app)
            notification_id: ID of delivered notification
            latency_seconds: Optional delivery latency in seconds

        Returns:
            True if metrics were published successfully
        """
        # Track delivery count
        success = MetricsService._publish_metric(
            metric_name=MetricsService.METRIC_NOTIFICATION_DELIVERED,
            value=1,
            unit='Count',
            dimensions={'Channel': channel}
        )

        # Track latency if provided
        if latency_seconds is not None:
            latency_success = MetricsService._publish_metric(
                metric_name=MetricsService.METRIC_DELIVERY_LATENCY,
                value=latency_seconds,
                unit='Seconds',
                dimensions={'Channel': channel}
            )
            success = success and latency_success

        return success

    @staticmethod
    def track_delivery_failure(
        channel: str,
        error_type: str,
        notification_id: int,
        is_retryable: bool = True
    ) -> bool:
        """
        Track failed notification delivery.

        Args:
            channel: Delivery channel (email, sms)
            error_type: Type of error (e.g., 'SMTPError', 'InvalidPhone')
            notification_id: ID of failed notification
            is_retryable: Whether the failure is retryable

        Returns:
            True if metric was published successfully
        """
        dimensions = {
            'Channel': channel,
            'ErrorType': error_type,
            'Retryable': str(is_retryable)
        }

        return MetricsService._publish_metric(
            metric_name=MetricsService.METRIC_NOTIFICATION_FAILED,
            value=1,
            unit='Count',
            dimensions=dimensions
        )

    @staticmethod
    def track_sms_cost(
        cost: Decimal,
        success: bool = True
    ) -> bool:
        """
        Track SMS delivery cost.

        Args:
            cost: Cost of SMS delivery (in USD)
            success: Whether SMS was delivered successfully

        Returns:
            True if metric was published successfully
        """
        dimensions = {
            'Status': 'Success' if success else 'Failed'
        }

        return MetricsService._publish_metric(
            metric_name=MetricsService.METRIC_SMS_COST,
            value=float(cost),
            unit='None',  # Currency amounts use 'None'
            dimensions=dimensions
        )

    @staticmethod
    def track_queue_depth(
        queue_name: str,
        depth: int
    ) -> bool:
        """
        Track Celery queue depth.

        Args:
            queue_name: Name of the queue (e.g., 'notifications', 'celery')
            depth: Number of pending tasks in queue

        Returns:
            True if metric was published successfully
        """
        return MetricsService._publish_metric(
            metric_name=MetricsService.METRIC_QUEUE_DEPTH,
            value=depth,
            unit='Count',
            dimensions={'Queue': queue_name}
        )

    @staticmethod
    def track_error_rate(
        component: str,
        error_count: int,
        total_count: int
    ) -> bool:
        """
        Track error rate for a component.

        Args:
            component: Component name (e.g., 'NotificationService', 'EmailService')
            error_count: Number of errors
            total_count: Total number of operations

        Returns:
            True if metric was published successfully
        """
        if total_count == 0:
            rate = 0.0
        else:
            rate = (error_count / total_count) * 100

        return MetricsService._publish_metric(
            metric_name=MetricsService.METRIC_ERROR_RATE,
            value=rate,
            unit='Percent',
            dimensions={'Component': component}
        )

    @staticmethod
    def track_batch_operation(
        operation: str,
        batch_size: int,
        success_count: int,
        duration_seconds: float
    ) -> bool:
        """
        Track batch operation metrics.

        Args:
            operation: Operation name (e.g., 'daily_digest', 'batch_create')
            batch_size: Total size of batch
            success_count: Number of successful operations
            duration_seconds: Total duration in seconds

        Returns:
            True if metrics were published successfully
        """
        dimensions = {'Operation': operation}

        # Track batch size
        size_success = MetricsService._publish_metric(
            metric_name='BatchSize',
            value=batch_size,
            unit='Count',
            dimensions=dimensions
        )

        # Track success count
        success_metric = MetricsService._publish_metric(
            metric_name='BatchSuccessCount',
            value=success_count,
            unit='Count',
            dimensions=dimensions
        )

        # Track duration
        duration_metric = MetricsService._publish_metric(
            metric_name='BatchDuration',
            value=duration_seconds,
            unit='Seconds',
            dimensions=dimensions
        )

        # Track success rate
        rate = (success_count / batch_size * 100) if batch_size > 0 else 100
        rate_metric = MetricsService._publish_metric(
            metric_name='BatchSuccessRate',
            value=rate,
            unit='Percent',
            dimensions=dimensions
        )

        return all([size_success, success_metric, duration_metric, rate_metric])


class MetricsCollector:
    """
    Helper class for collecting metrics over a period.

    Usage:
        with MetricsCollector('daily_digest') as collector:
            for user in users:
                try:
                    send_digest(user)
                    collector.success()
                except Exception:
                    collector.failure()
        # Metrics automatically published on exit
    """

    def __init__(self, operation: str):
        """
        Initialize metrics collector.

        Args:
            operation: Operation name for metrics
        """
        self.operation = operation
        self.total = 0
        self.successes = 0
        self.failures = 0
        self.start_time = None

    def __enter__(self):
        """Start collecting metrics."""
        self.start_time = timezone.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Publish collected metrics."""
        if self.start_time:
            duration = (timezone.now() - self.start_time).total_seconds()

            MetricsService.track_batch_operation(
                operation=self.operation,
                batch_size=self.total,
                success_count=self.successes,
                duration_seconds=duration
            )

        return False  # Don't suppress exceptions

    def success(self):
        """Record a successful operation."""
        self.total += 1
        self.successes += 1

    def failure(self):
        """Record a failed operation."""
        self.total += 1
        self.failures += 1
