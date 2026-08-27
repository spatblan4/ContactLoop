"""Compatibility entrypoint for the AWS Lambda default handler setting."""

from contact_brief.handler import lambda_handler

__all__ = ["lambda_handler"]
