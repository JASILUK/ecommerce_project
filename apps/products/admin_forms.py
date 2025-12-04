from django import forms
from cloudinary.uploader import upload
from .models import ProductGeneralImage, ProductColorImage


class ProductGeneralImageForm(forms.ModelForm):
    image_url = forms.URLField(
        required=False,
        label="Image URL",
        help_text="Paste image URL → auto upload to Cloudinary"
    )

    class Meta:
        model = ProductGeneralImage
        fields = ["image_url", "is_default"]   

    def save(self, commit=True):
        image_url = self.cleaned_data.get("image_url")

        if image_url:
            result = upload(image_url)
            self.instance.image = result["public_id"]

        return super().save(commit)


class ProductColorImageForm(forms.ModelForm):
    image_url = forms.URLField(
        required=False,
        label="Image URL",
        help_text="Paste image URL → auto upload to Cloudinary"
    )

    class Meta:
        model = ProductColorImage
        fields = ["image_url"]

    def save(self, commit=True):
        image_url = self.cleaned_data.get("image_url")

        if image_url:
            result = upload(image_url)
            self.instance.image = result["public_id"]

        return super().save(commit)
