"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase, RequestFactory

from datetime import date, timedelta
from decimal import Decimal
import mock
import nose.tools

from muckrock import factories
from muckrock.project import models, forms, views
from muckrock.test_utils import mock_middleware, http_get_response, http_post_response

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

test_title = u'Private Prisons'
test_description = (
    u'The prison industry is growing at an alarming rate. '
    'Even more alarming? The conditions inside prisions '
    'are growing worse while their tax-dollar derived '
    'profits are growing larger.')
test_image = SimpleUploadedFile(
    name='foo.gif',
    content=(b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,'
    '\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00'))


class TestProjectCreateView(TestCase):
    """Tests creating a project as a user."""
    def setUp(self):
        self.view = views.ProjectCreateView.as_view()
        self.url = reverse('project-create')

    def test_basic(self):
        """Basic users should not be able to GET the ProjectCreateView."""
        user = factories.UserFactory()
        response = http_get_response(self.url, self.view, user)
        eq_(response.status_code, 200,
            'Basic users should be able to GET the ProjectCreateView.')

    def test_anonymous(self):
        """Logged out users should not be able to GET the ProjectCreateView."""
        response = http_get_response(self.url, self.view, AnonymousUser())
        eq_(response.status_code, 302,
            'Anonymous users should not be able to GET the ProjectCreateView.')
        redirect_url = reverse('acct-login') + '?next=' + reverse('project-create')
        eq_(response.url, redirect_url,
            'The user should be redirected to the login page.')

    def test_post(self):
        """Posting a valid ProjectForm should create the project."""
        form = forms.ProjectCreateForm({
            'title': 'Cool Project',
            'summary': 'Yo my project is cooler than LIFE!',
            'image': test_image,
            'tags': 'dogs, cats',
            'private': True,
            'featured': True
        })
        ok_(form.is_valid(), 'The form should validate.')
        staff_user = factories.UserFactory(is_staff=True)
        response = http_post_response(self.url, self.view, form.data, staff_user)
        project = models.Project.objects.last()
        eq_(response.status_code, 302,
            'The response should redirect to the project when it is created.')
        ok_(staff_user in project.contributors.all(),
            'The current user should automatically be added as a contributor.')


class TestProjectEditView(TestCase):
    """Contributors and staff may edit a project."""
    def setUp(self):
        # We will start with a project that's already been made.
        # We will give that project a single contributor.
        self.contributor = factories.UserFactory()
        self.project = factories.ProjectFactory()
        self.project.contributors.add(self.contributor)
        self.project.save()
        self.factory = RequestFactory()
        self.kwargs = {
            'slug': self.project.slug,
            'pk': self.project.pk
        }
        self.url = reverse('project-edit', kwargs=self.kwargs)
        self.view = views.ProjectEditView.as_view()

    def test_staff(self):
        """Staff users should be able to edit projects."""
        staff_user = factories.UserFactory(is_staff=True)
        response = http_get_response(self.url, self.view, staff_user, **self.kwargs)
        eq_(response.status_code, 200)

    def test_contributor(self):
        """Contributors should be able to edit projects."""
        response = http_get_response(self.url, self.view, self.contributor, **self.kwargs)
        eq_(response.status_code, 200)

    @raises(Http404)
    def test_basic(self):
        """Basic users should not be able to edit projects."""
        user = factories.UserFactory()
        http_get_response(self.url, self.view, user, **self.kwargs)

    def test_anonymous(self):
        """Logged out users cannot edit projects."""
        response = http_get_response(self.url, self.view, AnonymousUser())
        redirect_url = reverse('acct-login') + '?next=' + self.url
        eq_(response.status_code, 302,
            'The user should be redirected.')
        eq_(response.url, redirect_url,
            'The user should be redirected to the login page.')

    def test_edit_description(self):
        """
        The description should be editable.
        When sending data, the 'edit' keyword should be set to 'description'.
        """
        desc = 'Lorem ipsum'
        data = {
            'title': self.project.title,
            'description': desc,
        }
        form = forms.ProjectUpdateForm(data, instance=self.project)
        ok_(form.is_valid(), 'The form should validate. %s' % form.errors)
        http_post_response(self.url, self.view, data, self.contributor, **self.kwargs)
        self.project.refresh_from_db()
        eq_(self.project.description, desc,
            'The description should be updated.')

    @mock.patch('muckrock.message.tasks.notify_project_contributor.delay')
    def test_add_contributors(self, mock_notify):
        """When adding contributors, each new contributor should get an email notification."""
        new_contributor = factories.UserFactory()
        data = {
            'title': self.project.title,
            'contributors': [self.contributor.pk, new_contributor.pk]
        }
        form = forms.ProjectUpdateForm(data, instance=self.project)
        ok_(form.is_valid(), 'The form should validate. %s' % form.errors)
        http_post_response(self.url, self.view, data, self.contributor, **self.kwargs)
        self.project.refresh_from_db()
        ok_(self.project.has_contributor(new_contributor))
        ok_(self.project.has_contributor(self.contributor))
        mock_notify.assert_called_once_with(new_contributor, self.project, self.contributor)

class TestProjectPublishView(TestCase):
    """Tests publishing a project."""
    def setUp(self):
        # We will start with a project that's already been made.
        self.project = factories.ProjectFactory(private=True, approved=False)
        self.contributor = factories.UserFactory()
        self.project.contributors.add(self.contributor)
        self.kwargs = {
            'slug': self.project.slug,
            'pk': self.project.pk
        }
        self.url = reverse('project-publish', kwargs=self.kwargs)
        self.view = views.ProjectPublishView.as_view()

    def test_staff(self):
        """Staff users should be able to publish projects."""
        staff_user = factories.UserFactory(is_staff=True)
        response = http_get_response(self.url, self.view, staff_user, **self.kwargs)
        eq_(response.status_code, 200)

    def test_contributor(self):
        """Contributors should be able to delete projects."""
        response = http_get_response(self.url, self.view, self.contributor, **self.kwargs)
        eq_(response.status_code, 200)

    @raises(Http404)
    def test_basic(self):
        """Basic users should not be able to delete projects."""
        user = factories.UserFactory()
        http_get_response(self.url, self.view, user, **self.kwargs)

    def test_anonymous(self):
        """Anonymous users cannot delete projects."""
        response = http_get_response(self.url, self.view, AnonymousUser(), **self.kwargs)
        redirect_url = reverse('acct-login') + '?next=' + self.url
        eq_(response.status_code, 302,
            'The user should be redirected.')
        eq_(response.url, redirect_url,
            'The user should be reidrected to the login screen.')

    def test_pending(self):
        """Projects that are pending review should reject access to the Publish view."""
        pending_project = factories.ProjectFactory(private=False, approved=False)
        pending_project.contributors.add(self.contributor)
        response = http_get_response(self.url, self.view, self.contributor, **{
            'slug': pending_project.slug,
            'pk': pending_project.pk
        })
        eq_(response.status_code, 302)
        eq_(response.url, pending_project.get_absolute_url(),
            'The user should be redirected to the project.')

    @mock.patch('muckrock.project.models.Project.publish')
    def test_post(self, mock_publish):
        """Posting a valid ProjectPublishForm should publish the project."""
        notes = 'Testing project publishing'
        form = forms.ProjectPublishForm({'notes': notes})
        ok_(form.is_valid(), 'The form should validate.')
        response = http_post_response(
            self.url,
            self.view,
            form.data,
            self.contributor,
            **self.kwargs)
        eq_(response.status_code, 302,
            'The user should be redirected.')
        eq_(response.url, self.project.get_absolute_url(),
            'The user should be redirected back to the project page.')
        mock_publish.assert_called_with(notes)


class TestProjectCrowdfundView(TestCase):
    """Tests the creation of a crowdfund for a project."""
    def setUp(self):
        self.project = factories.ProjectFactory(private=False, approved=True)
        self.url = reverse('project-crowdfund', kwargs={
            'slug': self.project.slug,
            'pk': self.project.pk
        })
        self.view = views.ProjectCrowdfundView.as_view()
        self.request_factory = RequestFactory()

    def test_post(self):
        """Posting data for a crowdfund should create it."""
        user = factories.UserFactory(is_staff=True)
        name = 'Project Crowdfund'
        description = 'A crowdfund'
        payment_required = 100
        payment_capped = True
        date_due = date.today() + timedelta(20)
        data = {
            'name': name,
            'description': description,
            'payment_required': payment_required,
            'payment_capped': payment_capped,
            'date_due': date_due
        }
        request = self.request_factory.post(self.url, data)
        request.user = user
        request = mock_middleware(request)
        response = self.view(request, slug=self.project.slug, pk=self.project.pk)
        self.project.refresh_from_db()
        eq_(self.project.crowdfunds.count(), 1,
            'A crowdfund should be created and added to the project.')
        crowdfund = self.project.crowdfunds.first()
        eq_(crowdfund.name, name)
        eq_(crowdfund.description, description)
        expected_payment_required = Decimal(payment_required + payment_required * .15) / 100
        eq_(crowdfund.payment_required, expected_payment_required,
            'Expected payment of %(expected).2f, actually %(actual).2f' % {
                'expected': expected_payment_required,
                'actual': crowdfund.payment_required
            })
        eq_(crowdfund.payment_capped, payment_capped)
        eq_(crowdfund.date_due, date_due)
        eq_(response.status_code, 302)


class TestProjectContributorView(TestCase):
    """Provides a list of just projects the user contributes to."""
    def setUp(self):
        self.user = factories.UserFactory()
        project = factories.ProjectFactory()
        project.contributors.add(self.user)
        self.kwargs = {'username': self.user.username}
        self.url = reverse('project-contributor', kwargs=self.kwargs)
        self.view = views.ProjectContributorView.as_view()

    def test_get(self):
        """The view should render, of course!"""
        response = http_get_response(self.url, self.view, self.user, **self.kwargs)
        eq_(response.status_code, 200, 'The view should return 200.')
