from django.db import models

class JobListing(models.Model):
    original_id = models.CharField(unique=True, max_length=128)
    job_title = models.CharField(max_length=128)
    job_location = models.CharField(max_length=256)
    company_name = models.CharField(max_length=256)
    company_url = models.URLField()
    date_posted = models.DateTimeField()
    job_description = models.CharField(max_length=4096)
    requirements = models.CharField(max_length=4096)
    company_description = models.CharField(max_length=4096, null=True, blank=True)
    python_description = models.CharField(max_length=4096, null=True, blank=True)
    contact_name = models.CharField(max_length=256)
    contact_email = models.EmailField()
    contact_other = models.CharField(max_length=1024)
    contact_web = models.URLField()
    telecommuting = models.BooleanField()
    other = models.CharField(max_length=1024) #for stuff we can't parse
    
    def __unicode__(self):
        return "%s - %s" % (self.company_name, self.job_location)
    
from django.contrib import admin
from django import forms
class JobListingAdmin(admin.ModelAdmin):

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(JobListingAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if 'description' in db_field.name or db_field.name == 'requirements':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        return formfield

admin.site.register(JobListing, JobListingAdmin)