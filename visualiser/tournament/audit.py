"""Helpers for recording request-driven model changes in the admin log."""

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.admin.utils import construct_change_message


def _form_change_message(form, formsets, add):
    """Build Django's message and record the form that caused the change.

    add indicates whether the main form represents a newly added object.
    """
    message = construct_change_message(form, formsets, add)
    # Django's History renderer ignores this entry, but it remains in the stored JSON.
    message.append({'form': {'name': form.__class__.__name__}})
    return message


def log_form_action(user, form, obj, action_flag, add=False):
    """Record one ModelForm action using Django's standard change message.

    Set add to True when the form created the object rather than changed it.
    """
    if not user.is_authenticated:
        return
    LogEntry.objects.log_actions(
        user_id=user.pk,
        queryset=[obj],
        action_flag=action_flag,
        change_message=_form_change_message(form, [], add),
        single_object=True,
    )


def log_formset_actions(user, formset):
    """Record changed, added, and deleted objects from a saved ModelFormSet."""
    if not user.is_authenticated:
        return
    form = formset.forms[0] if formset.forms else None
    changed_objects = [obj for obj, fields in formset.changed_objects]
    if changed_objects:
        LogEntry.objects.log_actions(
            user_id=user.pk,
            queryset=changed_objects,
            action_flag=CHANGE,
            change_message=_form_change_message(form, [formset], False),
        )
    if formset.new_objects:
        LogEntry.objects.log_actions(
            user_id=user.pk,
            queryset=formset.new_objects,
            action_flag=ADDITION,
            change_message=_form_change_message(form, [formset], False),
        )
    if formset.deleted_objects:
        LogEntry.objects.log_actions(
            user_id=user.pk,
            queryset=formset.deleted_objects,
            action_flag=DELETION,
            change_message=_form_change_message(form, [formset], False),
        )


def log_objects_action(user, objects, action_flag, change_message, form_name=None):
    """Record an action for objects that were not saved through a form."""
    if not user.is_authenticated:
        return
    if form_name:
        change_message = list(change_message)
        change_message.append({'form': {'name': form_name}})
    LogEntry.objects.log_actions(
        user_id=user.pk,
        queryset=objects,
        action_flag=action_flag,
        change_message=change_message,
    )


def log_objects_change(user, objects, fields, form_name=None):
    """Record a change with the fields changed by a custom form workflow."""
    log_objects_action(user, objects, CHANGE,
                       [{'changed': {'fields': fields}}],
                       form_name=form_name)
