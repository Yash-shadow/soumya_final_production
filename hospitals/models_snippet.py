class BillItem(models.Model):
    """Individual service claim in a bill."""
    bill = models.ForeignKey(Bill, related_name='items', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    claimed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.service.name} - {self.claimed_amount}"
