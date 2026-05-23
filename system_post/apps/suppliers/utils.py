from django.db import transaction, models


class SupplierInvoiceCounter(models.Model):
    prefix = models.CharField(max_length=10, unique=True)
    counter = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'suppliers_invoice_counter'

    def __str__(self):
        return f'{self.prefix}-{self.counter:06d}'


@transaction.atomic
def next_supplier_invoice_number(prefix='FAC-P'):
    counter, _ = SupplierInvoiceCounter.objects.select_for_update().get_or_create(prefix=prefix)
    counter.counter += 1
    counter.save(update_fields=['counter'])
    return f'{prefix}-{counter.counter:06d}'