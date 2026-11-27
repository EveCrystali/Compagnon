namespace PilouBureau;

// Gabarit rétro des boutons (Aventure, journal), en texte sans WPF pour que les tests le relisent (HabitBoutonTests).
// S'il ne se charge pas, GabaritBouton (FenetreAventure) rend null en silence et les boutons gardent l'habit Windows (texte illisible une fois désactivés).
// Un Setter de trigger ne peut viser qu'un élément nommé, pas un TranslateTransform : on remplace le RenderTransform.
public static class HabitBouton
{
    public const string Xaml = """
        <ControlTemplate xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                         xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" TargetType="Button">
          <Grid SnapsToDevicePixels="True">
            <Border x:Name="ombre" Background="#0a0d1a" Margin="3,3,-3,-3"/>
            <Border x:Name="fond" Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}"
                    BorderThickness="{TemplateBinding BorderThickness}" Padding="{TemplateBinding Padding}">
              <ContentPresenter HorizontalAlignment="{TemplateBinding HorizontalContentAlignment}" VerticalAlignment="Center"
                                RecognizesAccessKey="False"/>
            </Border>
          </Grid>
          <ControlTemplate.Triggers>
            <Trigger Property="IsMouseOver" Value="True">
              <Setter TargetName="fond" Property="BorderBrush" Value="#f69d50"/>
              <Setter TargetName="fond" Property="RenderTransform">
                <Setter.Value><TranslateTransform X="-1" Y="-1"/></Setter.Value>
              </Setter>
            </Trigger>
            <Trigger Property="IsKeyboardFocused" Value="True">
              <Setter TargetName="fond" Property="BorderBrush" Value="#b4dbff"/>
            </Trigger>
            <Trigger Property="IsPressed" Value="True">
              <Setter TargetName="fond" Property="RenderTransform">
                <Setter.Value><TranslateTransform X="2" Y="2"/></Setter.Value>
              </Setter>
              <Setter TargetName="ombre" Property="Visibility" Value="Hidden"/>
            </Trigger>
            <Trigger Property="IsEnabled" Value="False">
              <Setter Property="Opacity" Value="0.45"/>
            </Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
        """;
}
