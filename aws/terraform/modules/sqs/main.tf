# =============================================================================
# SQS Queue Module
# =============================================================================
# GAMP-5 Compliance:
# - Dead Letter Queue for explicit failure tracking (NO FALLBACK LOGIC)
# - Long polling for efficient message retrieval
# - Message retention for audit trail

# Main queue for job processing
resource "aws_sqs_queue" "main" {
  name                       = var.queue_name
  delay_seconds              = var.delay_seconds
  max_message_size           = var.max_message_size
  message_retention_seconds  = var.message_retention_seconds
  receive_wait_time_seconds  = var.receive_wait_time_seconds
  visibility_timeout_seconds = var.visibility_timeout_seconds

  # Server-side encryption
  sqs_managed_sse_enabled = true

  # Redrive policy to DLQ for failed messages
  # NO FALLBACK LOGIC: Failed messages go to DLQ (not silently dropped)
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Component = "queue"
    GAMP5     = "true"
  }
}

# Dead Letter Queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.queue_name}-dlq"
  message_retention_seconds = var.dlq_retention_seconds

  # Server-side encryption
  sqs_managed_sse_enabled = true

  tags = {
    Component = "dlq"
    GAMP5     = "true"
  }
}

# Allow main queue to send messages to DLQ
resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.main.arn]
  })
}
