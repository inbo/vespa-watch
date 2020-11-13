from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ExportMixin
from import_export.fields import Field
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from .models import Taxon, Nest, Individual, NestPicture, IndividualPicture, ManagementAction, IdentificationCard, \
    IndividualObservationWarning, NestObservationWarning, Profile


class ManagementActionResource(resources.ModelResource):
    class Meta:
        model = ManagementAction


class NestResource(resources.ModelResource):
    taxon_name = Field(attribute='taxon__name', column_name='taxon_name')

    class Meta:
        model = Nest


class IndividualResource(resources.ModelResource):
    taxon_name = Field(attribute='taxon__name', column_name='taxon_name')

    class Meta:
        model = Individual


class IdentificationCardInline(TranslationTabularInline):
    model = IdentificationCard
    max_num = 2


@admin.register(Taxon)
class TaxonAdmin(admin.ModelAdmin):

    inlines = (IdentificationCardInline, )


@admin.register(NestPicture)
class NestPictureAdmin(admin.ModelAdmin):
    list_display = ('observation', 'image', 'datetime')

@admin.register(IndividualPicture)
class IndividualPictureAdmin(admin.ModelAdmin):
    list_display = ('observation', 'image', 'datetime')

class NestPictureInline(admin.TabularInline):
    # We cannot add/edit/delete pictures of non-editable observations
    def has_add_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_add_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_delete_permission(request, obj=obj)

    model = NestPicture


class IndividualPictureInline(admin.TabularInline):
    # We cannot add/edit/delete pictures of non-editable observations
    def has_add_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_add_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_delete_permission(request, obj=obj)

    model = IndividualPicture


class IndividualObservationWarningInline(admin.TabularInline):
    model = IndividualObservationWarning


class NestObservationWarningInline(admin.TabularInline):
    model = NestObservationWarning


class DeleteObjectsOneByOneMixin():
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()


@admin.register(Nest)
class NestAdmin(DeleteObjectsOneByOneMixin, ExportMixin, admin.ModelAdmin):
    resource_class = NestResource

    # Some observations cannot be changed nor deleted
    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_in_admin:
            return False
        return super().has_change_permission(request, obj=obj)

    def get_readonly_fields(self, request, obj=None):
        r = super().get_readonly_fields(request, obj)
        if obj and not obj.taxon_can_be_locally_changed:
            r = r + ('taxon', )
        return r

    list_display = ('taxon', 'inaturalist_id', 'observation_time', 'latitude', 'longitude', 'municipality', 'originates_in_vespawatch', 'has_warnings', 'inat_vv_confirmed')
    readonly_fields = ('originates_in_vespawatch', 'created_at')

    list_filter = ('taxon', 'originates_in_vespawatch')

    inlines = [
        NestPictureInline,
        NestObservationWarningInline
    ]


@admin.register(Individual)
class IndividualAdmin(DeleteObjectsOneByOneMixin, ExportMixin, admin.ModelAdmin):
    resource_class = IndividualResource

    # Some observations cannot be changed nor deleted
    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_in_admin:
            return False
        return super().has_change_permission(request, obj=obj)

    def get_readonly_fields(self, request, obj=None):
        r = super().get_readonly_fields(request, obj)
        if obj and not obj.taxon_can_be_locally_changed:
            r = r + ('taxon', )
        return r

    list_display = ('taxon', 'inaturalist_id', 'observation_time', 'latitude', 'longitude', 'originates_in_vespawatch', 'has_warnings', 'inat_vv_confirmed')
    readonly_fields = ('originates_in_vespawatch', 'created_at')

    list_filter = ('taxon', 'originates_in_vespawatch')

    inlines = [
        IndividualPictureInline,
        IndividualObservationWarningInline
    ]


@admin.register(ManagementAction)
class ManagementActionAdmin(ExportMixin, admin.ModelAdmin):
    pass


class ProfileInline(admin.TabularInline):
    model = Profile


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile')
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notification')
    readonly_fields = ('user',)



@admin.register(IdentificationCard)
class IdentificationCardAdmin(TranslationAdmin):
    list_display = ('order', 'represented_taxon', 'represents_nest')
