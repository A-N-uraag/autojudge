from django import forms
from django.core.validators import RegexValidator, validate_email, EMPTY_VALUES


CONTEST_START_SOFT_END_INVALID = -1
CONTEST_SOFT_END_HARD_END_INVALID = +1
CONTEST_VALID = 0


def _check_valid_date(cleaned_data):
    cont_start = cleaned_data.get("contest_start")
    cont_soft_end = cleaned_data.get("contest_soft_end")
    cont_hard_end = cleaned_data.get("contest_hard_end")
    if cont_start and cont_soft_end and cont_hard_end:
        if cont_start > cont_soft_end:
            return CONTEST_START_SOFT_END_INVALID
        if cont_soft_end > cont_hard_end:
            return CONTEST_SOFT_END_HARD_END_INVALID
    return CONTEST_VALID


class MultiEmailField(forms.Field):
    """
    Subclass of forms.Field to support a list of email addresses.
    """
    description = 'Email addresses'

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(MultiEmailField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return []
        return [item.strip() for item in value.split(self.token) if item.strip()]

    def clean(self, value):
        value = self.to_python(value)
        if value in EMPTY_VALUES and self.required:
            raise forms.ValidationError('This field is required.')
        for email in value:
            try:
                validate_email(email)
            except forms.ValidationError:
                raise forms.ValidationError("'{}' is not a valid email address.".format(email))
        return value


class IndexStringForm(forms.Form):
    """
    Form for editing index string
    """
    index_str = forms.CharField(label='Index String', min_length=1, max_length=25,
                                   strip=True,
                                   widget=forms.TextInput(attrs={'class': 'form-control'}),
                                   help_text='Enter string to replace \'Contest\' string.')
    """Index String"""

    index_str_plural = forms.CharField(label='Plural Index String', min_length=1,
                                   max_length=25, strip=True,
                                   widget=forms.TextInput(attrs={'class': 'form-control'}),
                                   help_text='Enter plural form of above string \
                                             (to replace \'Contests\' string).')
    """Plural Index String"""

class NewContestForm(forms.Form):
    """
    Form for creating a new Contest.
    """

    contest_name = forms.CharField(label='Contest name', max_length=50, strip=True,
                                   widget=forms.TextInput(attrs={'class': 'form-control'}),
                                   help_text='Enter the name of the contest.')
    """Contest Name"""

    contest_start = forms.DateTimeField(label='Start Date',
                                        widget=forms.DateTimeInput(attrs={'class': 'form-control'}),
                                        help_text='Specify when the contest begins.')
    """Contest Start Timestamp"""

    contest_soft_end = forms.DateTimeField(label='Soft End Date for contest',
                                           widget=forms.DateTimeInput(
                                               attrs={'class': 'form-control'}),
                                           help_text='Specify after when would you like to \
                                                      penalize submissions.')
    """Contest Soft End Timestamp"""

    contest_hard_end = forms.DateTimeField(label='Hard End Date for contest',
                                           widget=forms.DateTimeInput(
                                               attrs={'class': 'form-control'}),
                                           help_text='Specify when the contest completely ends.')
    """Contest Hard End Timestamp"""

    penalty = forms.DecimalField(label='Penalty', min_value=0.0, max_value=1.0,
                                 widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                 help_text='Enter a penalty factor between 0 and 1.')
    """Contest Penalty factor"""

    is_public = forms.BooleanField(label='Is this contest public?', required=False)
    """Contest is_public property"""

    enable_leaderboard = forms.BooleanField(label='Enable leaderboard', required=False,
                                             initial=True)
    """Contest enable_leaderboard property"""

    enable_linter_score = forms.BooleanField(label='Enable linter scoring',
                                             required=False)
    """Contest enable_linter_score property"""

    enable_poster_score = forms.BooleanField(label='Enable poster scoring',
                                             required=False, initial=True)
    """Contest enable_poster_score property"""

    def clean(self):
        cleaned_data = super().clean()
        error = _check_valid_date(cleaned_data)
        if error == CONTEST_START_SOFT_END_INVALID:
            err_ = forms.ValidationError("Contest cannot end before it starts!",
                                         code='invalid')
            self.add_error('contest_start', err_)
            self.add_error('contest_soft_end', err_)

        elif error == CONTEST_SOFT_END_HARD_END_INVALID:
            err_ = forms.ValidationError(
                       "The final deadline cannot be before the soft deadline.", code='invalid')
            self.add_error('contest_soft_end', err_)
            self.add_error('contest_hard_end', err_)


class UpdateContestForm(forms.Form):
    """
    Form to update the timeline of the Contest
    """

    contest_start = forms.DateTimeField(label='Start Date', required=False,
                                        widget=forms.DateTimeInput(attrs={'class': 'form-control'}),
                                        help_text='Specify when the contest begins.')
    """Contest Start Timestamp"""

    contest_soft_end = forms.DateTimeField(label='Soft End Date', required=False,
                                           widget=forms.DateTimeInput(
                                               attrs={'class': 'form-control'}),
                                           help_text='Specify after when would you like to \
                                                      penalize submissions.')
    """Contest Soft End Timestamp"""

    contest_hard_end = forms.DateTimeField(label='Hard End Date', required=False,
                                           widget=forms.DateTimeInput(
                                               attrs={'class': 'form-control'}),
                                           help_text='Specify when the contest completely ends.')
    """Contest Hard End Timestamp"""

    show_leaderboard = forms.BooleanField(label='Display leaderboard', required=False,
                                            help_text='Specify whether leaderboard should be \
                                                        displayed.')
    """Contest show_leaderboard property"""

    show_private_tests = forms.BooleanField(label='Display private test cases', required=False,
                                            help_text='Specify whether private test cases should be \
                                                        displayed.')
    """Contest show_private_tests property"""

    def clean(self):
        cleaned_data = super().clean()
        error = _check_valid_date(cleaned_data)
        if error == CONTEST_START_SOFT_END_INVALID:
            err_ = forms.ValidationError("Contest cannot end before it starts!",
                                         code='invalid')
            self.add_error('contest_start', err_)
            self.add_error('contest_soft_end', err_)

        elif error == CONTEST_SOFT_END_HARD_END_INVALID:
            err_ = forms.ValidationError(
                       "The final deadline cannot be before the soft deadline.", code='invalid')
            self.add_error('contest_soft_end', err_)
            self.add_error('contest_hard_end', err_)


class AddPersonToContestForm(forms.Form):
    """
    Form to add a Person to a Contest.
    """

    emails = MultiEmailField(
        label='Emails',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='Enter emails separated using commas')
    """Email ID of the person"""


class DeletePersonFromContestForm(forms.Form):
    """
    Form to remove a Person from a Contest.
    """

    email = forms.EmailField(label='Email', widget=forms.HiddenInput())
    """Email ID of the person"""


class NewProblemForm(forms.Form):
    """
    Form for adding a new Problem.
    """

    code = forms.CharField(label='Code', max_length=10, widget=forms.TextInput(
                           attrs={'class': 'form-control'}),
                           validators=[RegexValidator(r'^[a-z0-9]+$')],
                           help_text='Enter a alphanumeric code in lowercase letters as a \
                                      unique identifier for the problem.')
    """Problem Code Field"""

    name = forms.CharField(label='Title', max_length=50, strip=True,
                           widget=forms.TextInput(attrs={'class': 'form-control'}),
                           help_text='Give a catchy problem name.')
    """Problem Name Field"""

    statement = forms.CharField(label='Statement', strip=True, widget=forms.HiddenInput(),
                                help_text='Provide a descriptive statement of the problem.')
    """Problem Statement Field"""

    input_format = forms.CharField(label='Input Format', strip=True, widget=forms.HiddenInput(),
                                   help_text='Give a lucid format for the input that a \
                                              participant should expect.')
    """Problem Input Format Field"""

    output_format = forms.CharField(label='Output Format', strip=True, widget=forms.HiddenInput(),
                                    help_text='Give a lucid format for the output that a \
                                               participant should follow.')
    """Problem Output Format Field"""

    difficulty = forms.IntegerField(label='Difficulty',
                                    widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                    min_value=0, max_value=5, initial=0,
                                    help_text='Specify a difficulty level between 1 and 5 for \
                                               the problem. If this is unknown, leave it as 0.')
    """Problem Difficulty Field"""

    time_limit = forms.DurationField(label='Time Limit (in milliseconds)',
                                     widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                     initial=1000, help_text='Specify a time limit in milliseconds \
                                                           for the execution of the program.')
    """Problem Time limit"""

    memory_limit = forms.IntegerField(label='Memory Limit (in KB)',
                                      widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                      initial=10240, min_value=0,
                                      help_text='Specify a memory limit in MB for the execution \
                                                 of the program.If not specified(set to 0) memory limit will default to 1 KB')
    """Problem Memory limit"""

    submission_limit = forms.IntegerField(label='Submission Limit', min_value=1,
                                 max_value=1000, required=False, initial=1000,
                                 widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                 help_text='Enter the maximum number of submissions allowed \
                                            for each participant (between 1 and 1000).')
    """Problem Submission Limit"""

    file_exts = forms.CharField(label='Permitted File extensions for submissions',
                                widget=forms.TextInput(attrs={'class': 'form-control'}),
                                max_length=100, required=False,
                                validators=[RegexValidator(r'^\.[a-zA-Z0-9]+(,\.[a-zA-Z0-9]+)*$')],
                                empty_value='.py,.cpp',
                                help_text='Give a comma separated list of extensions accepted \
                                           for submissions.')
    """Problem File Extensions"""

    enable_evaluation = forms.BooleanField(label='Enable evaluations for submissions',
                                           required=False,
                                           initial=True)
    """Problem enable_evaluation property"""

    clang_checks_choices = [
        ('all', 'All checks'),
        ('string-all-check', 'All string checks'),
        ('strcmp-check', 'strcmp check'),
        ('strcpy-check', 'strcpy check'),
        ('strlen-check', 'strlen check'),
        ('sys-all-check', 'All system call checks'),
    ]
    
    clang_checks = forms.MultipleChoiceField(label='Clang Checks',
                                   widget = forms.CheckboxSelectMultiple,
                                   choices = clang_checks_choices,
                                   required=False,
                                   initial = clang_checks_choices[0],
                                   help_text='Enable clang checks to run.')
    """Problem Clang Tool Flags"""

    is_cmdline = forms.BooleanField(label='Enable command line arguments',
                                    required=False, initial=False)
    """Problem is_cmdline property"""

    starting_code = forms.FileField(label='Starting code',
                                    widget=forms.FileInput(attrs={'class': 'form-control-file'}),
                                    allow_empty_file=False, required=False,
                                    help_text='Upload some starting code to help participants \
                                               get started.')
    """Problem Starting code"""

    input_files = forms.FileField(label='Input files',
                                  widget=forms.FileInput(attrs={'class': 'form-control-file'}),
                                  allow_empty_file=False, required=False,
                                  help_text='Upload zip archive containing files that \
                                             the submissions should read.')
    """Problem input files"""

    max_score = forms.IntegerField(label='Maximum score',
                                   widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                   initial=10, min_value=0,
                                   help_text='Specify the maximum score that passing testcase \
                                              for this problem would award.')
    """Problem Max Score"""

    compilation_script = forms.FileField(label='Compilation script',
                                         widget=forms.FileInput(
                                             attrs={'class': 'form-control-file'}),
                                         allow_empty_file=False, required=False,
                                         help_text='Upload a custom compilation script.')
    """Problem Compilation Script"""

    test_script = forms.FileField(label='Testing script',
                                  widget=forms.FileInput(attrs={'class': 'form-control-file'}),
                                  allow_empty_file=False, required=False,
                                  help_text='Upload a custom testing script.')
    """Problem Test Script"""


class EditProblemForm(forms.Form):
    """
    Form for editing an existing problem.
    """

    name = forms.CharField(label='Title', max_length=50, strip=True,
                           widget=forms.TextInput(attrs={'class': 'form-control'}),
                           help_text='Give a catchy problem name.')
    """Problem Name Field"""

    statement = forms.CharField(label='Statement', strip=True, widget=forms.HiddenInput(),
                                help_text='Provide a descriptive statement of the problem.')
    """Problem Statement Field"""

    input_format = forms.CharField(label='Input Format', strip=True, widget=forms.HiddenInput(),
                                   help_text='Give a lucid format for the input that a \
                                              participant should expect.')
    """Problem Input Format Field"""

    output_format = forms.CharField(label='Output Format', strip=True, widget=forms.HiddenInput(),
                                    help_text='Give a lucid format for the output that a \
                                               participant should follow.')
    """Problem Output Format Field"""

    difficulty = forms.IntegerField(label='Difficulty',
                                    widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                    initial=0, min_value=0, max_value=5,
                                    help_text='Specify a difficulty level between 1 and 5 for \
                                               the problem. If this is unknown, leave it as 0.')
    """Problem Difficulty Field"""

class CloseProblemForm(forms.Form):
    """
    Form for closing submissions for a problem.
    """
    is_closed = forms.BooleanField(label='Close submissions', required=False,
                                   help_text='Specify whether submissions for the problem \
                                              should be closed.')
    """Problem is_closed property"""

class NewSubmissionForm(forms.Form):
    """
    Form to create a new Submission.
    """
    
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        super(NewSubmissionForm, self).__init__(*args, **kwargs)
        self.fields['file_type'] = forms.ChoiceField(label='File type', choices=choices)

    file_type = forms.ChoiceField()
    """Choices of file type"""

    submission_file = forms.FileField(label='Choose file', required=True, allow_empty_file=False,
                                      widget=forms.FileInput(attrs={'class': 'custom-file-input'}),
                                      help_text='Upload your submission.')
    """Submission File"""


class AddTestCaseForm(forms.Form):
    """
    Form to create a new TestCase
    """

    test_type = forms.ChoiceField(label='Test type', choices=[
        ('public', 'Public'),
        ('private', 'Private')
    ])
    """TestCase Type"""

    input_file = forms.FileField(label='Input file', allow_empty_file=False, required=True,
                                 help_text='Upload input for test case.')
    """TestCase Input"""

    output_file = forms.FileField(label='Output file', allow_empty_file=False, required=True,
                                  help_text='Upload output for test case.')
    """TestCase Output"""


class NewCommentForm(forms.Form):
    """
    Form to add a new comment
    """

    participant_email = forms.EmailField(label='Email', widget=forms.HiddenInput())
    """Email of participant"""

    comment = forms.CharField(label='Comment', required=True, widget=forms.Textarea(
        attrs={'class': 'form-control', 'rows': 2}))
    """Comment content"""


class AddPosterScoreForm(forms.Form):
    """
    Form to add poster score for a submission
    """

    score = forms.IntegerField(
        label='Poster Score', widget=forms.NumberInput(attrs={'class': 'form-control'}),
        initial=0)
    """Score field"""
