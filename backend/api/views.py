from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser, Subscribe

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShortRecipeSerializer, TagSerializer,
                          UserSubscriptionsSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @staticmethod
    def send_message(ingredients):
        """Формирование файла со списком покупок."""
        shopping_list = 'Список покупок:\n'
        for ingredient in ingredients:
            shopping_list += (
                f'{ingredient["ingredient__name"]}  - '
                f'{ingredient["amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}\n'
            )
        file = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}"'
        return response

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        return self.send_message(ingredients)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        """Добавление/удаление из избранного."""
        return self._add_to_list_or_delete(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Добавление/удаление из корзины."""
        return self._add_to_list_or_delete(ShoppingCart, request.user, pk)

    def _add_to_list_or_delete(self, model, user, pk):
        """Вспомогательный метод для добавления/удаления."""
        if self.request.method == 'POST':
            if model.objects.filter(user=user, recipe__id=pk).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            recipe = get_object_or_404(Recipe, id=pk)
            model.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            obj = model.objects.filter(user=user, recipe__id=pk)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'errors': 'Рецепт уже удален!'},
                            status=status.HTTP_400_BAD_REQUEST)
        return None


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями и подписками."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        user = request.user
        queryset = CustomUser.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserSubscriptionsSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка от автора."""
        user = request.user
        author = get_object_or_404(CustomUser, pk=id)

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscribe.objects.create(user=user, author=author)
            serializer = UserSubscriptionsSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscribe.objects.filter(user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Вы не были подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None
