from django.contrib import admin

from .models import Species, Nest, Individual, NestPicture, IndividualPicture, ManagementAction

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    readonly_fields = ('inaturalist_pull_taxon_ids', 'inaturalist_push_taxon_id')


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


@admin.register(Nest)
class NestAdmin(admin.ModelAdmin):
    # Some observations cannot be changed nor deleted
    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_delete_permission(request, obj=obj)

    list_display = ('species', 'inaturalist_id', 'observation_time', 'latitude', 'longitude')
    readonly_fields = ('originates_in_vespawatch',)

    list_filter = ('species', 'originates_in_vespawatch')

    inlines = [
        NestPictureInline,
    ]

@admin.register(Individual)
class IndividualAdmin(admin.ModelAdmin):
    # Some observations cannot be changed nor deleted
    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_delete_permission(request, obj=obj)

    list_display = ('species', 'inaturalist_id', 'observation_time', 'latitude', 'longitude')
    readonly_fields = ('originates_in_vespawatch',)

    list_filter = ('species', 'originates_in_vespawatch')

    inlines = [
        IndividualPictureInline,
    ]

@admin.register(ManagementAction)
class ManagementActionAdmin(admin.ModelAdmin):
    pass