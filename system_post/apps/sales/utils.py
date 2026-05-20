from django.db import transaction, models


class InvoiceCounter(models.Model):
    prefix = models.CharField(max_length=10, unique=True)
    counter = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'sales_invoice_counter'


@transaction.atomic
def next_invoice_number(prefix='VNT'):
    counter, _ = InvoiceCounter.objects.select_for_update().get_or_create(prefix=prefix)
    counter.counter += 1
    counter.save(update_fields=['counter'])
    return f'{prefix}-{counter.counter:06d}'
